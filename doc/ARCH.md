# KNU MES 시스템 — 아키텍처 문서

> Kubernetes 기반 클라우드 네이티브 MES (Manufacturing Execution System) 아키텍처

---

## 1. 시스템 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                     VM (Ubuntu aarch64)                          │
│                  192.168.64.5 / c1master1                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Kubernetes Cluster (kubeadm v1.30+)          │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │
│  │  │ mes-frontend │  │   mes-api     │  │    postgres      │ │  │
│  │  │ nginx:alpine │  │ python:3.9   │  │ PostgreSQL 15    │ │  │
│  │  │  :80 (30173) │  │  :80 (30461) │  │  :5432           │ │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘ │  │
│  │         │                 │                  │             │  │
│  │         │   /api/* proxy  │   DATABASE_URL   │             │  │
│  │         │────────────────>│─────────────────>│             │  │
│  │         │                 │                  │             │  │
│  │  ┌──────┴──────────────────┴───────────────────┐          │  │
│  │  │           Cilium eBPF CNI + Hubble          │          │  │
│  │  └─────────────────────────────────────────────┘          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                    │
      :30173 (Web)        :30461 (API)      :30080 (Auth)
           │                    │              │
    ┌──────┴────────────────────┴──────────────┴──┐
    │              사용자 브라우저                   │
    │   http://192.168.64.5:30173                  │
    │   Keycloak OIDC 로그인 → JWT Bearer Token    │
    └──────────────────────────────────────────────┘
```

---

## 2. 기술 스택

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **인프라** | Kubernetes (kubeadm) | v1.28+ | 컨테이너 오케스트레이션 |
| **네트워크** | Cilium eBPF + Hubble | 최신 | CNI, 네트워크 정책, 플로우 모니터링 |
| **인증** | Keycloak (OIDC/PKCE) | 24.0.5 | SSO 인증 서버 |
| **DB** | PostgreSQL | 15 | 관계형 데이터 저장소 (19개 테이블) |
| **백엔드** | Python FastAPI | 0.109 | REST API 서버 (37개 엔드포인트) |
| **프론트엔드** | React 19 + Vite + Tailwind CSS 4 | 최신 | SPA 웹 UI (14개 메뉴) |
| **프론트엔드 서빙** | nginx:alpine | 최신 | 정적 파일 서빙 + API 리버스 프록시 |
| **CI/CD** | Jenkins (Jenkinsfile) | - | 린트 → 테스트 → 빌드 → 배포 파이프라인 |
| **배포 방식** | ConfigMap 기반 | - | Docker 빌드 없이 코드 배포 |

---

## 3. Kubernetes 리소스 구성

### 3.1 Pod / Deployment

| Deployment | Image | Port | NodePort | 역할 |
|------------|-------|------|----------|------|
| `mes-frontend` | `nginx:alpine` | 80 | **30173** | React 빌드 파일 서빙, API 리버스 프록시 |
| `mes-api` | `python:3.9-slim` | 80 | **30461** | FastAPI REST API 서버 |
| `postgres` | `postgres:15` | 5432 | - (ClusterIP) | PostgreSQL 데이터베이스 |
| `keycloak` | `keycloak` | 8080 | **30080** | Keycloak OIDC 인증 서버 |

### 3.2 ConfigMap

| ConfigMap | 내용 | 용도 |
|-----------|------|------|
| `api-code` | `app.py` + `api_modules/*.py` (27개 파일) | 백엔드 소스 코드를 Pod에 마운트 |
| `frontend-build` | `dist/` 디렉토리 (빌드 결과물) | React 빌드 파일을 nginx에 마운트 |
| `nginx-config` | `default.conf` | nginx 설정 (프록시 룰 포함) |

### 3.3 Secret / Storage

| 리소스 | 내용 |
|--------|------|
| `db-credentials` (Secret) | `DATABASE_URL=postgresql://postgres:mes1234@postgres:5432/mes_db` |
| `postgres-pv` (PersistentVolume) | 1Gi, hostPath `/mnt/data` |
| `postgres-pvc` (PersistentVolumeClaim) | postgres-pv에 바인딩 |
| `pip-cache` (hostPath Volume) | `/mnt/pip-cache` — API Pod의 pip 패키지 캐시 (재기동 시 다운로드 생략) |

### 3.4 배포 방식: ConfigMap 기반 (Docker 빌드 불필요)

```
소스 코드 수정
    │
    ├─ 백엔드: kubectl create configmap api-code --from-file=...
    │          kubectl rollout restart deployment mes-api
    │
    └─ 프론트엔드: npm run build
                   kubectl create configmap frontend-build --from-file=dist/
                   kubectl rollout restart deployment mes-frontend
```

기존 Docker 이미지를 수정하지 않고, ConfigMap만 갱신하여 코드를 배포합니다.
- `api-code` ConfigMap → `/mnt` 에 마운트 → 컨테이너 시작 시 `/app/`으로 복사 → pip install (캐시 활용) → 실행
- `frontend-build` ConfigMap → `/usr/share/nginx/html` 에 마운트 → nginx가 즉시 서빙
- `pip-cache` hostPath (`/mnt/pip-cache`) → `/pip-cache` 에 마운트 → pip 패키지 캐시 재사용

### 3.5 심층 동작 원리: Kubernetes 내부 메커니즘

#### 3.5.1 Pod 생성 시 내부 흐름

사용자가 `kubectl apply -f mes-api.yaml`을 실행하면 다음 과정이 순차적으로 발생합니다.

```
┌──────────┐   REST/HTTPS    ┌───────────┐   watch     ┌───────────┐
│ kubectl  │────────────────>│ API Server│<────────────│ Scheduler │
│ (client) │                 │ (kube-    │             │           │
└──────────┘                 │  apiserver)│             └─────┬─────┘
                             └─────┬─────┘                   │
                                   │ persist                  │ bind Pod
                                   ▼                         │ to Node
                             ┌───────────┐                   │
                             │   etcd    │                   │
                             │ (3-node   │                   │
                             │  cluster) │                   │
                             └───────────┘                   │
                                                             ▼
                             ┌───────────┐   gRPC      ┌───────────┐
                             │containerd │<────────────│  kubelet  │
                             │(runtime)  │             │ (노드 에이전트)│
                             └─────┬─────┘             └───────────┘
                                   │ create
                                   ▼
                             ┌───────────┐
                             │   Pod     │
                             │ (컨테이너) │
                             └───────────┘
```

**상세 단계:**

1. **kubectl → API Server**: kubectl이 Deployment YAML을 JSON으로 직렬화하고 `POST /apis/apps/v1/namespaces/default/deployments`로 전송. API Server는 인증(ServiceAccount 토큰/kubeconfig 인증서) → 인가(RBAC) → Admission Control(Validating/Mutating Webhook) 순으로 처리
2. **API Server → etcd**: 검증 통과 후 Deployment 오브젝트를 etcd에 키-값 형태(`/registry/deployments/default/mes-api`)로 저장. etcd는 Raft 합의 알고리즘으로 과반수 노드에 복제 후 커밋
3. **Deployment Controller**: kube-controller-manager 내 Deployment Controller가 etcd watch를 통해 변경을 감지하고 ReplicaSet을 생성
4. **ReplicaSet Controller**: 원하는 replicas 수만큼 Pod 오브젝트를 생성 (이 시점에서 Pod의 `spec.nodeName`은 비어있음)
5. **Scheduler**: `nodeName`이 비어 있는 Pod을 감지 → 노드 필터링(Predicates: 리소스 충족, taints/tolerations, affinity) → 스코어링(Priorities: 리소스 밸런싱, spread) → 최적 노드 선택 → Pod의 `spec.nodeName`을 업데이트
6. **kubelet**: 해당 노드의 kubelet이 자신에게 바인딩된 Pod을 감지 → CRI(Container Runtime Interface) gRPC 호출로 containerd에 컨테이너 생성 요청
7. **containerd**: OCI 스펙에 따라 컨테이너 생성 → runc가 Linux namespace(pid, net, mnt, uts, ipc), cgroup, seccomp 프로파일을 설정하여 격리된 프로세스 실행

#### 3.5.2 Deployment rollout restart 내부 동작

`kubectl rollout restart deployment mes-api` 실행 시:

```
시간축 →

ReplicaSet v1 (기존)         ReplicaSet v2 (신규)
┌─────────────────────┐      ┌─────────────────────┐
│ Pod-A (Running) ────────── │                     │  ← v2 RS 생성
│ Pod-A (Running) ────────── │ Pod-B (Pending)     │  ← v2 Pod 스케줄링
│ Pod-A (Running) ────────── │ Pod-B (Running)  ✓  │  ← v2 Ready
│ Pod-A (Terminating) ────── │ Pod-B (Running)     │  ← v1 Pod 제거 시작
│                     │      │ Pod-B (Running)     │  ← v1 완전 종료
└─────────────────────┘      └─────────────────────┘
  replicas: 1→0                replicas: 0→1
```

**핵심 메커니즘:**

1. **Pod Template Hash 변경**: rollout restart는 Deployment의 `spec.template.metadata.annotations`에 `kubectl.kubernetes.io/restartedAt` 타임스탬프를 추가하여 Pod Template의 해시값을 변경시킴
2. **새 ReplicaSet 생성**: Deployment Controller가 변경된 Pod Template 해시를 감지하고 새로운 ReplicaSet(v2)을 생성
3. **롤링 업데이트 전략**: `strategy.rollingUpdate`에 따라 동작
   - `maxSurge` (기본 25%): 원하는 replicas 수 대비 동시에 추가 생성 가능한 Pod 수
   - `maxUnavailable` (기본 25%): 업데이트 중 사용 불가능한 Pod의 최대 수
4. **Pod 종료 과정**: 기존 Pod에 `SIGTERM` 전송 → `terminationGracePeriodSeconds`(기본 30초) 대기 → 미종료 시 `SIGKILL` 전송
5. **Volume 재마운트**: 새 Pod 생성 시 kubelet이 ConfigMap Volume을 새로 마운트하여 최신 코드 반영

#### 3.5.3 NodePort 서비스 트래픽 라우팅 원리

외부 사용자가 `http://192.168.64.5:30173`에 접근할 때 내부 동작:

```
┌─────────────────┐
│ 사용자 브라우저   │
│ :30173 요청      │
└────────┬────────┘
         │ TCP SYN
         ▼
┌────────────────────────────────────────────────────┐
│  Node (192.168.64.5)                               │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  kube-proxy (iptables/IPVS 모드)             │  │
│  │                                              │  │
│  │  iptables 규칙 체인:                          │  │
│  │  PREROUTING → KUBE-SERVICES                  │  │
│  │    → KUBE-NODEPORTS                          │  │
│  │      → KUBE-SVC-xxxx (서비스 가상 IP)         │  │
│  │        → KUBE-SEP-xxxx (엔드포인트, DNAT)     │  │
│  │                                              │  │
│  │  DNAT: dst 192.168.64.5:30173               │  │
│  │     →  dst 10.0.0.15:80 (Pod IP:Port)       │  │
│  └──────────────────────────────────────────────┘  │
│                        │                           │
│                        ▼                           │
│  ┌──────────────────────────────┐                  │
│  │ Pod: mes-frontend            │                  │
│  │ IP: 10.0.0.15, Port: 80     │                  │
│  │ (nginx:alpine 컨테이너)      │                  │
│  └──────────────────────────────┘                  │
└────────────────────────────────────────────────────┘
```

**iptables 모드 동작 원리:**

1. kube-proxy는 API Server를 watch하여 Service/Endpoints 변경을 감지
2. 변경 시 iptables 규칙을 동적으로 재생성 (netfilter 커널 모듈 활용)
3. `KUBE-SVC-*` 체인에서 `statistic mode random probability` 규칙으로 복수 Pod 간 로드 밸런싱
4. `KUBE-SEP-*` 체인에서 DNAT(Destination NAT)으로 목적지를 Pod IP:Port로 변환
5. conntrack 테이블에 세션 기록 → 응답 패킷은 자동으로 역변환(SNAT)

**IPVS 모드와의 차이**: IPVS는 커널의 L4 로드밸런서를 사용하여 O(1) 룩업을 제공. iptables는 규칙이 선형 탐색(O(n))이므로 서비스가 수천 개일 때 성능 저하 발생

#### 3.5.4 ConfigMap이 Pod에 마운트되는 메커니즘

```
┌─────────────────────────────────────────────────────┐
│  kubelet (노드 에이전트)                              │
│                                                     │
│  ┌─────────────────┐     ┌────────────────────────┐ │
│  │ Volume Manager  │     │ Volume Plugin:         │ │
│  │                 │────>│ configMapVolumePlugin  │ │
│  │ - Desired State │     │                        │ │
│  │ - Actual State  │     │ 1. API Server에서      │ │
│  │ - Reconcile()   │     │    ConfigMap 데이터 조회 │ │
│  └─────────────────┘     │ 2. tmpfs에 파일 생성    │ │
│                          │ 3. atomic write:       │ │
│                          │    ..data_tmp → ..data │ │
│                          │    (symlink swap)      │ │
│                          └────────────────────────┘ │
│                                     │               │
│                                     ▼               │
│  ┌──────────────────────────────────────────┐       │
│  │ Pod 내부 (/mnt/api-code/)                │       │
│  │                                          │       │
│  │ app.py → ..data/app.py                   │       │
│  │ api_modules/ → ..data/api_modules/       │       │
│  │ ..data → ..2026_03_12_10_30_00.123456    │       │
│  │          (실제 데이터 디렉토리 symlink)     │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

**마운트 과정 상세:**

1. kubelet의 Volume Manager가 Pod spec에서 `configMap` 타입 볼륨을 파싱
2. `configMapVolumePlugin`이 API Server에 ConfigMap 데이터를 요청
3. 노드의 tmpfs(메모리 기반 파일시스템)에 ConfigMap의 각 키를 파일로 생성
4. **Atomic Update**: 데이터 디렉토리를 타임스탬프 기반 이름으로 생성 → `..data` 심볼릭 링크를 atomic하게 교체 (rename syscall) → 파일 일관성 보장
5. **Projected Volume**: 여러 소스(ConfigMap, Secret, Downward API)를 하나의 볼륨으로 합칠 때 사용. kubelet이 각 소스를 개별 조회 후 단일 디렉토리로 병합

### 3.6 심층 동작 원리: ConfigMap 기반 배포 메커니즘

#### 왜 Docker 빌드 없이 배포가 가능한가

전통적인 컨테이너 배포에서는 "코드 변경 → Docker 이미지 빌드 → 레지스트리 푸시 → 이미지 Pull → 컨테이너 생성" 과정이 필요합니다. 본 시스템은 이 과정을 근본적으로 단축합니다.

```
[전통적 방식]                        [ConfigMap 방식 (본 시스템)]
코드 수정                            코드 수정
   ↓                                    ↓
Dockerfile 기반 이미지 빌드            kubectl create configmap
(COPY, pip install 등 레이어 생성)       (etcd에 소스코드 저장)
   ↓                                    ↓
레지스트리에 Push (수백 MB)            rollout restart
   ↓                                    ↓
Pull + 컨테이너 생성                   새 Pod가 base image(python:3.9)에서 기동
                                         ↓
소요: 3~10분                          ConfigMap 볼륨 마운트 → 코드 복사 → pip install(캐시)
                                      소요: 30~60초
```

**원리**: 컨테이너 이미지는 "런타임 환경(OS, 인터프리터)"만 제공하고, 실제 애플리케이션 코드는 ConfigMap Volume으로 외부에서 주입합니다. 이는 "코드 = 설정"이라는 관점에서 Kubernetes의 ConfigMap을 확장 활용한 패턴입니다.

#### ConfigMap 크기 제한과 대응

- **제한**: etcd의 단일 value 크기 제한으로 ConfigMap은 **1MB**를 초과할 수 없음 (etcd의 `--max-request-bytes` 기본값 1.5MB, 인코딩 오버헤드 감안)
- **현재 상태**: `api-code` ConfigMap은 약 27개 Python 파일(합계 200~400KB)으로 제한 내
- **우회 방법**:
  1. ConfigMap을 모듈 단위로 분할 (`api-code-core`, `api-code-ai` 등)
  2. Binary 데이터는 `binaryData` 필드에 Base64 인코딩 저장 (단, 크기 제한은 동일)
  3. 코드가 1MB를 초과하면 PersistentVolume + init container 패턴으로 전환 필요

#### rollout restart 시 Pod 재생성 상세 과정

```
시간 →
t=0    kubectl rollout restart deployment mes-api
t=0.1  API Server가 Deployment annotation 업데이트 → etcd 저장
t=0.3  Deployment Controller가 새 ReplicaSet 생성
t=0.5  Scheduler가 새 Pod를 노드에 바인딩

t=1    kubelet이 새 Pod 감지:
       ├─ 1a. containerd에 python:3.9-slim 이미지 확인 (로컬 캐시 Hit)
       ├─ 1b. ConfigMap Volume 마운트 (/mnt/api-code/)
       ├─ 1c. hostPath Volume 마운트 (/pip-cache/)
       └─ 1d. Secret Volume 마운트 (db-credentials)

t=2    컨테이너 시작 → entrypoint/command 실행:
       ├─ cp -r /mnt/api-code/* /app/    (ConfigMap → 작업 디렉토리)
       ├─ pip install -r requirements.txt --cache-dir /pip-cache
       │   └─ 캐시 Hit: 패키지 재다운로드 없이 wheel에서 직접 설치
       └─ uvicorn app:app --host 0.0.0.0 --port 80

t=15   새 Pod Ready (Health Check 통과)
t=16   기존 Pod에 SIGTERM 전송
t=16   Service Endpoints에서 기존 Pod 제거 + 새 Pod 등록
t=46   기존 Pod 완전 종료 (gracePeriod 30초 경과 또는 프로세스 종료)
```

#### pip cache hostPath 볼륨의 작동 원리

```
┌─────────────────────────────────────────┐
│  Node Filesystem                        │
│  /mnt/pip-cache/                        │
│  ├── wheels/                            │
│  │   ├── fastapi-0.109.0-py3-none-any.whl│
│  │   ├── uvicorn-0.27.0-py3-none-any.whl│
│  │   └── ...                            │
│  └── http/                              │
│      └── (PyPI 응답 캐시)                │
└──────────────┬──────────────────────────┘
               │ hostPath mount
               ▼
┌──────────────────────────────────────┐
│  Pod: mes-api                        │
│  /pip-cache/ (volumeMount)           │
│                                      │
│  pip install --cache-dir /pip-cache  │
│  → 캐시 디렉토리에서 .whl 파일 확인   │
│  → HTTP 캐시에서 304 Not Modified     │
│  → 네트워크 다운로드 생략              │
└──────────────────────────────────────┘
```

hostPath는 노드의 로컬 파일시스템 경로를 Pod에 직접 마운트합니다. Pod이 삭제/재생성되어도 노드의 `/mnt/pip-cache/`는 유지되므로, pip 패키지 캐시가 재기동 간에 보존됩니다. 이를 통해 `pip install` 시간을 수 분에서 수 초로 단축합니다.

### 3.7 심층 동작 원리: Cilium eBPF 네트워크

#### 3.7.1 eBPF란 무엇인가

eBPF(extended Berkeley Packet Filter)는 **Linux 커널 내에서 실행되는 샌드박스 가상 머신**입니다. 커널 소스 코드를 수정하거나 커널 모듈을 로드하지 않고도, 커널의 다양한 hook point에 사용자 정의 프로그램을 안전하게 삽입할 수 있습니다.

```
┌──────────────────────────────────────────────────────────────┐
│  User Space                                                  │
│  ┌────────────┐    ┌────────────────┐    ┌────────────────┐  │
│  │ Cilium     │    │ cilium-agent   │    │ Hubble        │  │
│  │ CLI/API    │    │ (DaemonSet)    │    │ (Observer)    │  │
│  └─────┬──────┘    └───────┬────────┘    └───────┬────────┘  │
│        │                   │ BPF syscall         │            │
│========│===================│=====================│============│
│  Kernel Space              ▼                     │            │
│  ┌─────────────────────────────────────────────┐ │            │
│  │  eBPF Virtual Machine                       │ │            │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────┐ │ │            │
│  │  │Verifier │→│JIT Compiler│→│ Native Code│ │ │            │
│  │  │(안전성  │  │(x86/ARM  │  │(커널 내    │ │ │            │
│  │  │ 검증)   │  │ 네이티브) │  │ 직접 실행) │ │ │            │
│  │  └─────────┘  └──────────┘  └────────────┘ │ │            │
│  └────────────────────┬────────────────────────┘ │            │
│                       │ attach                   │ perf/ring  │
│                       ▼                          │ buffer     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │            │
│  │ TC hook  │  │ XDP hook │  │ socket   │      │            │
│  │(트래픽   │  │(NIC 드라  │  │ hook     │──────┘            │
│  │ 제어)    │  │ 이버 수준)│  │          │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

**eBPF 프로그램 실행 과정:**
1. C 코드로 작성된 eBPF 프로그램을 LLVM/Clang이 eBPF 바이트코드로 컴파일
2. `bpf()` 시스템 콜로 커널에 로드
3. **Verifier**가 프로그램 안전성 검증: 무한 루프 없음, 메모리 범위 초과 없음, 허용된 헬퍼 함수만 호출
4. **JIT Compiler**가 바이트코드를 CPU 네이티브 명령어(x86_64/ARM64)로 변환 → 커널 함수에 근접한 성능
5. hook point(TC, XDP, socket 등)에 attach하여 이벤트 발생 시 자동 실행

#### 3.7.2 기존 iptables CNI vs Cilium eBPF 데이터 경로 비교

```
[기존 iptables 기반 CNI (예: Calico iptables 모드, kube-proxy)]

  패킷 수신 → NIC driver → netfilter PREROUTING
                              ↓
                    KUBE-SERVICES 체인 (선형 탐색 O(n))
                              ↓
                    KUBE-SVC-xxxx 체인
                              ↓
                    KUBE-SEP-xxxx (DNAT)
                              ↓
                    conntrack 테이블 기록
                              ↓
                    FORWARD 체인 (NetworkPolicy 규칙)
                              ↓
                    bridge/veth → Pod

  문제점:
  - 서비스 수 증가 시 iptables 규칙 수 = O(서비스 × 엔드포인트) → 수만 개
  - 규칙 업데이트 시 전체 체인 재작성 (full-replace) → 수 초 소요
  - conntrack 테이블 race condition → 패킷 드랍 가능


[Cilium eBPF 방식]

  패킷 수신 → NIC driver → TC ingress hook
                              ↓
                    eBPF 프로그램 실행 (O(1) 해시 룩업)
                              ↓
                    BPF Map에서 서비스 → 엔드포인트 조회
                              ↓
                    패킷 헤더 직접 수정 (DNAT)
                              ↓
                    BPF redirect → 목적지 Pod의 veth로 직접 전달
                    (netfilter/iptables 체인 완전 우회)

  장점:
  - O(1) 해시맵 룩업으로 서비스 수에 무관한 성능
  - 규칙 변경 시 BPF Map만 원자적 업데이트 → 밀리초 단위
  - conntrack 불필요 → 패킷 드랍 제거
  - XDP를 사용하면 드라이버 레벨에서 패킷 처리 가능 (더 빠름)
```

#### 3.7.3 Cilium의 패킷 처리 과정

본 MES 시스템에서 프론트엔드 Pod이 백엔드 Pod으로 API 요청을 보낼 때:

```
mes-frontend Pod (10.0.0.15)           mes-api Pod (10.0.0.22)
        │                                      ▲
        │ HTTP GET /api/items                  │
        ▼                                      │
┌──────────────────┐                ┌──────────────────┐
│ veth (Pod 측)    │                │ veth (Pod 측)    │
└────────┬─────────┘                └────────▲─────────┘
         │                                   │
┌────────▼─────────┐                ┌────────┴─────────┐
│ veth (호스트 측) │                │ veth (호스트 측) │
│                  │                │                  │
│ TC egress hook   │                │ TC ingress hook  │
│ ┌──────────────┐ │                │ ┌──────────────┐ │
│ │ eBPF 프로그램│ │                │ │ eBPF 프로그램│ │
│ │              │ │                │ │              │ │
│ │ 1.Identity   │ │  bpf_redirect │ │ 5.Identity   │ │
│ │   조회       │ │ ──────────────>│ │   검증       │ │
│ │ 2.Policy     │ │  (직접 전달,   │ │ 6.Policy     │ │
│ │   평가       │ │   커널 스택    │ │   평가       │ │
│ │ 3.Service    │ │   우회)        │ │ 7.패킷 전달  │ │
│ │   DNAT       │ │                │ │   또는 드랍  │ │
│ │ 4.CT 기록    │ │                │ │              │ │
│ └──────────────┘ │                │ └──────────────┘ │
└──────────────────┘                └──────────────────┘
```

**각 단계 설명:**

1. **Identity 조회**: Cilium은 각 Pod/Service에 숫자 Identity를 부여. 소스 Pod의 Security Identity를 BPF Map에서 O(1)으로 조회
2. **Policy 평가**: CiliumNetworkPolicy에 따라 이 Identity가 목적지로 트래픽을 보낼 수 있는지 BPF Map에서 확인
3. **Service DNAT**: 목적지가 Service ClusterIP인 경우, BPF Map에서 백엔드 Pod IP:Port로 변환 (kube-proxy 대체)
4. **Connection Tracking**: BPF Map 기반 자체 conntrack으로 세션 추적 (커널 conntrack 불필요)
5. **`bpf_redirect()`**: 목적지 veth의 ifindex로 패킷을 직접 전달. 커널 네트워크 스택(routing, netfilter)을 완전히 우회하여 지연시간 단축

#### 3.7.4 Hubble이 네트워크 플로우를 수집하는 원리

```
┌────────────────────────────────────────────────────────────┐
│  Node                                                      │
│                                                            │
│  ┌──────────────────────┐                                  │
│  │ Cilium Agent         │                                  │
│  │ (DaemonSet)          │                                  │
│  │                      │     perf event /                 │
│  │  eBPF 프로그램이      │     ring buffer                  │
│  │  패킷 처리 시         │◄────────────────┐               │
│  │  이벤트 발생          │                 │               │
│  │                      │     ┌───────────┴──────────┐    │
│  │  ┌────────────────┐  │     │ eBPF 프로그램         │    │
│  │  │ Hubble         │  │     │ (TC hook에 attach)    │    │
│  │  │ (내장 Observer)│  │     │                      │    │
│  │  │                │  │     │ send_trace_notify()  │    │
│  │  │ - Flow 파싱    │  │     │ send_policy_verdict()│    │
│  │  │ - 버퍼 저장    │  │     │ send_drop_notify()   │    │
│  │  │   (ring buf)   │  │     └──────────────────────┘    │
│  │  └───────┬────────┘  │                                  │
│  └──────────┼───────────┘                                  │
│             │ gRPC (unix socket)                           │
│             ▼                                              │
│  ┌──────────────────────┐                                  │
│  │ Hubble Relay         │                                  │
│  │ (Deployment)         │                                  │
│  │                      │                                  │
│  │ - 모든 노드의         │                                  │
│  │   Hubble Observer에  │                                  │
│  │   gRPC 연결          │                                  │
│  │ - Flow 데이터 집계    │                                  │
│  │ - 외부 gRPC API 제공  │                                  │
│  └──────────┬───────────┘                                  │
└─────────────┼──────────────────────────────────────────────┘
              │ gRPC
              ▼
┌──────────────────────┐     REST/JSON     ┌──────────────┐
│ k8s_service.py       │────────────────>│ 프론트엔드     │
│ (mes-api Pod 내)     │                  │ NETWORK_FLOW  │
│                      │                  │ 메뉴          │
│ hubble observe 또는   │                  └──────────────┘
│ gRPC client로 조회   │
└──────────────────────┘
```

**데이터 흐름 상세:**

1. eBPF 프로그램이 패킷을 처리할 때마다 `send_trace_notify()` 헬퍼를 호출하여 perf event buffer에 이벤트 기록
2. 이벤트에는 소스/목적지 Identity, IP:Port, 프로토콜, 판정(forwarded/dropped), L7 정보(HTTP method/path) 포함
3. Cilium Agent 내장 Hubble Observer가 perf buffer를 poll하여 이벤트를 파싱하고 내부 ring buffer(기본 4096 플로우)에 저장
4. Hubble Relay가 모든 노드의 Observer에 gRPC 스트리밍 연결을 유지하며 플로우를 중앙 집계
5. `k8s_service.py`가 Hubble Relay의 gRPC API (또는 `hubble observe` CLI)를 호출하여 플로우 데이터를 조회
6. 프론트엔드의 NETWORK_FLOW 메뉴가 5초 간격으로 `/api/network/flows`를 폴링하여 실시간 서비스맵과 플로우 테이블을 렌더링

---

## 4. 백엔드 아키텍처

### 4.1 모듈 구조

```
app.py                          ← FastAPI 메인 라우터 (37개 엔드포인트)
│
├── api_modules/
│   ├── database.py             ← DB 연결 풀 (ThreadedConnectionPool)
│   │
│   ├── mes_auth.py             ← FN-001~003: 인증/권한
│   ├── mes_items.py            ← FN-004~007: 품목 관리
│   ├── mes_bom.py              ← FN-008~009: BOM 관리
│   ├── mes_process.py          ← FN-010~012: 공정/라우팅
│   ├── mes_equipment.py        ← FN-013~014, 032~034: 설비
│   ├── mes_plan.py             ← FN-015~017: 생산계획
│   ├── mes_work.py             ← FN-020~024: 작업지시/실적
│   ├── mes_quality.py          ← FN-025~027: 품질관리
│   ├── mes_inventory.py        ← FN-029~031: 재고관리
│   ├── mes_reports.py          ← FN-035~037: 리포트
│   │
│   ├── mes_ai_prediction.py    ← FN-018~019: AI 수요예측
│   ├── mes_defect_predict.py   ← FN-028: AI 불량예측
│   │
│   ├── k8s_service.py          ← Hubble API, Pod/서비스맵 조회
│   ├── sys_logic.py            ← 인프라 상태 (CPU/메모리)
│   │
│   ├── mes_dashboard.py        ← 대시보드 데이터
│   ├── mes_service.py          ← 서비스 유틸리티
│   ├── mes_master.py           ← 기준정보 유틸리티
│   ├── mes_production.py       ← 생산 유틸리티
│   ├── mes_execution.py        ← 실행 추적
│   ├── mes_work_order.py       ← 작업지시 유틸리티
│   ├── mes_inventory_status.py ← 재고 상태
│   ├── mes_inventory_movement.py ← 재고 이동
│   ├── mes_material_receipt.py ← 자재 입고
│   ├── mes_logistics.py        ← 물류 유틸리티
│   └── mes_logic.py            ← 비즈니스 로직
```

### 4.2 DB 연결 방식

```python
# database.py — 커넥션 풀링
ThreadedConnectionPool(minconn=2, maxconn=10, dsn=DATABASE_URL)

# 사용 패턴
conn = get_conn()       # 풀에서 커넥션 획득
try:
    cursor = conn.cursor()
    cursor.execute(SQL, params)
    ...
finally:
    release_conn(conn)  # 풀에 반환
```

- `get_conn()` / `release_conn()`: 직접 커넥션 관리
- `query_db(sql, params)`: RealDictCursor로 간편 쿼리
- `db_connection()`: 컨텍스트 매니저 (with문)

### 4.3 심층 동작 원리: JWT 인증 플로우

#### 4.3.1 로그인 및 토큰 발급 과정

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│ 브라우저  │                    │ mes-api  │                    │PostgreSQL│
│ (React)  │                    │ (FastAPI)│                    │          │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                              │
     │ POST /api/auth/login          │                              │
     │ {user_id, password}           │                              │
     │──────────────────────────────>│                              │
     │                               │                              │
     │                               │ SELECT * FROM users          │
     │                               │ WHERE user_id = ?            │
     │                               │─────────────────────────────>│
     │                               │                              │
     │                               │ {user_id, password_hash,     │
     │                               │  name, role, ...}            │
     │                               │<─────────────────────────────│
     │                               │                              │
     │                               │ bcrypt.checkpw(              │
     │                               │   password.encode(),         │
     │                               │   password_hash.encode()     │
     │                               │ )                            │
     │                               │                              │
     │                               │ [비밀번호 일치 시]             │
     │                               │ jwt.encode(                  │
     │                               │   payload={                  │
     │                               │     "user_id": "admin",      │
     │                               │     "role": "admin",         │
     │                               │     "exp": now + 24h,        │
     │                               │     "iat": now               │
     │                               │   },                         │
     │                               │   key=JWT_SECRET,            │
     │                               │   algorithm="HS256"          │
     │                               │ )                            │
     │                               │                              │
     │ 200 OK                        │                              │
     │ {"token": "eyJhbGciOi..."}    │                              │
     │<──────────────────────────────│                              │
     │                               │                              │
     │ localStorage.setItem(         │                              │
     │   "token", token)             │                              │
     │                               │                              │
```

#### 4.3.2 JWT 토큰 구조 (header.payload.signature)

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.    ← Header (Base64URL)
eyJ1c2VyX2lkIjoiYWRtaW4iLCJyb2xlIjoi... ← Payload (Base64URL)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c ← Signature

Header (디코딩):    {"alg": "HS256", "typ": "JWT"}
Payload (디코딩):   {"user_id": "admin", "role": "admin", "exp": 1741996800, "iat": 1741910400}
Signature:          HMAC-SHA256(base64url(header) + "." + base64url(payload), JWT_SECRET)
```

#### 4.3.3 API 요청 시 JWT 검증 흐름

```
┌──────────┐                         ┌──────────────────────────────────────┐
│ 브라우저  │  GET /api/items         │ mes-api (FastAPI)                    │
│          │  Authorization:         │                                      │
│          │  Bearer eyJhbGci...     │                                      │
└────┬─────┘                         └────┬─────────────────────────────────┘
     │                                    │
     │───────────────────────────────────>│
     │                                    │
     │                              ┌─────▼──────────────────────────────┐
     │                              │ 1. Authorization 헤더 파싱          │
     │                              │    "Bearer eyJhbGci..." → 토큰 추출│
     │                              ├────────────────────────────────────┤
     │                              │ 2. 토큰을 "." 기준으로 3분할        │
     │                              │    [header, payload, signature]    │
     │                              ├────────────────────────────────────┤
     │                              │ 3. 서명 검증 (HMAC-SHA256)          │
     │                              │    expected = HMAC-SHA256(         │
     │                              │      header + "." + payload,      │
     │                              │      JWT_SECRET                   │
     │                              │    )                              │
     │                              │    expected == received signature?│
     │                              │    → 위조/변조 감지                 │
     │                              ├────────────────────────────────────┤
     │                              │ 4. Payload 디코딩 (Base64URL)      │
     │                              │    → JSON 파싱                     │
     │                              ├────────────────────────────────────┤
     │                              │ 5. 만료 시간 확인                   │
     │                              │    exp > current_timestamp ?      │
     │                              │    → 만료 시 401 Unauthorized      │
     │                              ├────────────────────────────────────┤
     │                              │ 6. 사용자 정보 추출                  │
     │                              │    user_id, role → 요청 컨텍스트   │
     │                              └─────┬──────────────────────────────┘
     │                                    │
     │  200 OK / 401 Unauthorized         │
     │<───────────────────────────────────│
```

**PyJWT 내부 동작:**
- `jwt.decode()` 호출 시 내부적으로 `_validate_claims()`가 `exp`, `iat`, `nbf` 등 등록 클레임을 검증
- HMAC-SHA256 서명: Python의 `hmac` 모듈이 OpenSSL의 `HMAC()` 함수를 호출하여 커널의 crypto API 활용
- Base64URL 인코딩: 표준 Base64에서 `+` → `-`, `/` → `_`, 패딩 `=` 제거 (URL-safe)
- 서명 비교 시 `hmac.compare_digest()`로 타이밍 공격(timing attack) 방지 (상수 시간 비교)

### 4.4 심층 동작 원리: DB 커넥션 풀 내부 동작

#### 4.4.1 psycopg2 ThreadedConnectionPool 동작 원리

```
┌───────────────────────────────────────────────────────────┐
│  ThreadedConnectionPool                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  _pool (list): 사용 가능한 커넥션 목록               │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐          ┌──────┐      │  │
│  │  │conn-1│ │conn-2│ │conn-3│   ...    │conn-n│      │  │
│  │  └──────┘ └──────┘ └──────┘          └──────┘      │  │
│  │                                                     │  │
│  │  _used (dict): 현재 사용 중인 커넥션 {key: conn}    │  │
│  │                                                     │  │
│  │  _rused (dict): 역매핑 {id(conn): key}              │  │
│  │                                                     │  │
│  │  minconn = 2   ← 풀 생성 시 미리 열어두는 최소 수    │  │
│  │  maxconn = 10  ← 동시 사용 가능한 최대 커넥션 수     │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────┐           │  │
│  │  │ threading.Lock (뮤텍스)               │           │  │
│  │  │ - getconn() / putconn() 시 획득       │           │  │
│  │  │ - 동시 접근으로부터 _pool, _used 보호  │           │  │
│  │  └──────────────────────────────────────┘           │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

**ThreadedConnectionPool vs SimpleConnectionPool:**
- `SimpleConnectionPool`: 단일 스레드 전용, 뮤텍스 없음
- `ThreadedConnectionPool`: 내부적으로 `threading.Lock`을 사용하여 `getconn()`과 `putconn()` 호출을 직렬화. FastAPI는 uvicorn의 thread pool에서 동기 엔드포인트를 실행하므로 멀티스레드 안전한 `ThreadedConnectionPool` 필수

#### 4.4.2 커넥션 획득/반환 라이프사이클

```
요청 스레드 A                        ThreadedConnectionPool
     │                                       │
     │ get_conn()                             │
     │──────────────────────────────────────>│
     │                                       │ Lock.acquire()
     │                                       │ _pool에서 conn pop
     │                                       │ _used[key] = conn
     │                                       │ Lock.release()
     │ conn 반환                              │
     │<──────────────────────────────────────│
     │                                       │
     │ cursor = conn.cursor()                │
     │ cursor.execute("SELECT ...")           │
     │ results = cursor.fetchall()            │
     │ conn.commit()                          │
     │                                       │
     │ release_conn(conn)                     │
     │──────────────────────────────────────>│
     │                                       │ Lock.acquire()
     │                                       │ _used에서 제거
     │                                       │ conn 상태 확인:
     │                                       │   정상 → _pool에 push
     │                                       │   에러 → conn.close() + 새 conn 생성
     │                                       │ Lock.release()
     │                                       │

     [예외 발생 시]
     │ conn에서 예외 발생                      │
     │ finally: release_conn(conn)            │
     │──────────────────────────────────────>│
     │                                       │ conn.rollback() 호출
     │                                       │ _pool에 반환 (재사용 가능)
```

#### 4.4.3 커넥션 풀 고갈 시 현상과 대응

```
상황: maxconn=10, 동시 요청 15개 발생

요청 1~10:  정상적으로 커넥션 획득 (풀에서 pop)
요청 11~15: _pool이 비어 있고 _used 수 == maxconn

  → ThreadedConnectionPool.getconn() 내부:
    if len(self._used) >= self.maxconn:
        raise PoolError("connection pool exhausted")

  → FastAPI에서 500 Internal Server Error 반환
```

**대응 방안:**
1. `maxconn` 값을 예상 동시 요청 수에 맞게 조정 (본 시스템: 10)
2. 커넥션 사용 시간 최소화: 쿼리 완료 즉시 `release_conn()` 호출
3. 커넥션 누수 방지: 반드시 `try/finally` 또는 컨텍스트 매니저 패턴 사용
4. PostgreSQL 측 `max_connections` (기본 100)과의 균형 고려

#### 4.4.4 PostgreSQL Wire Protocol 기초

```
┌──────────┐                              ┌──────────────┐
│ psycopg2 │                              │ PostgreSQL   │
│ (client) │                              │ (server)     │
└────┬─────┘                              └──────┬───────┘
     │                                           │
     │  StartupMessage                           │
     │  {protocol: 3.0, user, database}          │
     │──────────────────────────────────────────>│
     │                                           │
     │  AuthenticationMD5Password                │
     │  {salt: 4 bytes}                          │
     │<──────────────────────────────────────────│
     │                                           │
     │  PasswordMessage                          │
     │  md5(md5(password+user)+salt)             │
     │──────────────────────────────────────────>│
     │                                           │
     │  AuthenticationOk                         │
     │  ParameterStatus (server_version, ...)    │
     │  BackendKeyData (pid, secret_key)         │
     │  ReadyForQuery ('I' = idle)               │
     │<──────────────────────────────────────────│
     │                                           │
     │  Query                                    │
     │  "SELECT * FROM items WHERE ..."          │
     │──────────────────────────────────────────>│
     │                                           │
     │  RowDescription (컬럼 메타데이터)           │
     │  DataRow (행 데이터) × N                   │
     │  CommandComplete ("SELECT 20")            │
     │  ReadyForQuery ('I')                      │
     │<──────────────────────────────────────────│
```

**프로토콜 특징:**
- TCP 기반 바이너리 프로토콜 (기본 포트 5432)
- 메시지 형식: `[type: 1byte][length: 4bytes][payload: N bytes]`
- **Simple Query**: SQL 문자열 직접 전송 (파싱→계획→실행 매번 수행)
- **Extended Query**: Prepare → Bind → Execute 분리 (준비된 문장 재사용, SQL Injection 방지)
- psycopg2의 `cursor.execute(sql, params)`는 내부적으로 Extended Query 프로토콜을 사용하여 파라미터를 서버 측에서 바인딩

### 4.5 심층 동작 원리: FastAPI 요청 처리 파이프라인

#### 4.5.1 ASGI 서버에서 엔드포인트까지의 전체 경로

```
┌─────────────────────────────────────────────────────────────────────┐
│  요청 처리 파이프라인                                                 │
│                                                                     │
│  ┌──────────────────┐                                               │
│  │ uvicorn          │  ASGI 서버 (libuv/asyncio 이벤트 루프)         │
│  │                  │  - TCP 소켓 accept                             │
│  │ (uvloop 또는     │  - HTTP 파싱 (httptools/h11)                   │
│  │  asyncio)        │  - ASGI scope/receive/send 생성                │
│  └────────┬─────────┘                                               │
│           │ await app(scope, receive, send)                         │
│           ▼                                                         │
│  ┌──────────────────┐                                               │
│  │ Starlette        │  ASGI 프레임워크 (FastAPI의 기반)               │
│  │ (ASGI App)       │                                               │
│  └────────┬─────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 미들웨어 체인 (양파 모델 — 요청은 안쪽으로, 응답은 바깥으로)    │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │ ① CORSMiddleware                                      │  │   │
│  │  │   - Origin 헤더 확인                                    │  │   │
│  │  │   - OPTIONS preflight → 즉시 200 응답                  │  │   │
│  │  │   - 허용된 Origin이면 CORS 헤더 추가                    │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐  │  │   │
│  │  │  │ ② TrustedHostMiddleware (선택)                   │  │  │   │
│  │  │  │  ┌────────────────────────────────────────────┐  │  │  │   │
│  │  │  │  │ ③ ServerErrorMiddleware                    │  │  │   │   │
│  │  │  │  │   - 예외 → 500 응답 변환                    │  │  │   │   │
│  │  │  │  │  ┌──────────────────────────────────────┐  │  │  │   │   │
│  │  │  │  │  │ ④ ExceptionMiddleware                │  │  │  │   │   │
│  │  │  │  │  │   - HTTPException → JSON 에러 응답   │  │  │  │   │   │
│  │  │  │  │  │  ┌────────────────────────────────┐  │  │  │  │   │   │
│  │  │  │  │  │  │ ⑤ Router (Starlette)          │  │  │  │  │   │   │
│  │  │  │  │  │  │   - URL 패턴 매칭              │  │  │  │  │   │   │
│  │  │  │  │  │  │   - 경로 파라미터 추출          │  │  │  │  │   │   │
│  │  │  │  │  │  │  ┌──────────────────────────┐  │  │  │  │  │   │   │
│  │  │  │  │  │  │  │ ⑥ Dependency Injection  │  │  │  │  │  │   │   │
│  │  │  │  │  │  │  │   → Endpoint Handler    │  │  │  │  │  │   │   │
│  │  │  │  │  │  │  └──────────────────────────┘  │  │  │  │  │   │   │
│  │  │  │  │  │  └────────────────────────────────┘  │  │  │  │   │   │
│  │  │  │  │  └──────────────────────────────────────┘  │  │  │   │   │
│  │  │  │  └────────────────────────────────────────────┘  │  │   │   │
│  │  │  └──────────────────────────────────────────────────┘  │   │   │
│  │  └────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.5.2 CORS 미들웨어의 요청 처리 방식

CORS(Cross-Origin Resource Sharing)는 브라우저의 Same-Origin Policy를 제어하는 메커니즘입니다.

```
[Preflight 요청 — 브라우저가 자동 발생 (POST/PUT/DELETE 등)]

브라우저                            FastAPI CORSMiddleware
  │                                       │
  │ OPTIONS /api/items                    │
  │ Origin: http://192.168.64.5:30173     │
  │ Access-Control-Request-Method: POST   │
  │ Access-Control-Request-Headers:       │
  │   Content-Type, Authorization         │
  │──────────────────────────────────────>│
  │                                       │
  │                                       │ Origin이 CORS_ORIGINS에 포함?
  │                                       │   → 포함: 200 + CORS 헤더
  │                                       │   → 미포함: 400 Bad Request
  │                                       │
  │ 200 OK                                │
  │ Access-Control-Allow-Origin:          │
  │   http://192.168.64.5:30173           │
  │ Access-Control-Allow-Methods:         │
  │   GET, POST, PUT, DELETE              │
  │ Access-Control-Allow-Headers:         │
  │   Content-Type, Authorization         │
  │ Access-Control-Max-Age: 600           │
  │<──────────────────────────────────────│
  │                                       │
  │ [Preflight 통과 후 실제 요청]          │
  │ POST /api/items                       │
  │ Origin: http://192.168.64.5:30173     │
  │ Authorization: Bearer eyJ...          │
  │──────────────────────────────────────>│
  │                                       │ → 미들웨어 체인 → 핸들러 실행
  │ 201 Created                           │
  │ Access-Control-Allow-Origin:          │
  │   http://192.168.64.5:30173           │
  │<──────────────────────────────────────│
```

**본 시스템의 CORS 구성:**
- `CORS_ORIGINS` 환경변수에 허용할 Origin 목록을 지정 (`env.sh`에서 자동 생성)
- nginx 프록시를 통해 같은 Origin에서 API를 호출하면 CORS가 불필요하지만, 개발 환경(Vite dev server :5173)에서는 CORS가 필요

#### 4.5.3 의존성 주입(Depends)의 내부 동작

FastAPI의 `Depends()`는 호출 시점에 의존성 트리를 해석하고 결과를 캐싱합니다.

```python
# 의존성 체인 예시
def get_db():             # 의존성 1: DB 커넥션
    conn = get_conn()
    try:
        yield conn        # 엔드포인트에 conn 주입
    finally:
        release_conn(conn) # 응답 후 정리

def get_current_user(     # 의존성 2: JWT 인증 (의존성 1 불필요)
    authorization: str = Header(...)
):
    token = authorization.split(" ")[1]
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return payload

@app.get("/api/items")
def get_items(
    user = Depends(get_current_user),  # 의존성 주입
    conn = Depends(get_db)              # 의존성 주입
):
    ...
```

**내부 동작 과정:**

```
요청 수신
    │
    ▼
┌───────────────────────────────────────────┐
│ FastAPI Dependency Resolver               │
│                                           │
│ 1. 엔드포인트의 함수 시그니처 분석          │
│    → Depends() 파라미터 식별              │
│                                           │
│ 2. 의존성 트리 구성 (DAG)                  │
│    get_items                              │
│    ├── get_current_user (독립)             │
│    └── get_db (독립)                       │
│                                           │
│ 3. 독립 의존성은 (비동기면) 동시 실행 가능   │
│                                           │
│ 4. Generator 의존성 (yield 사용):          │
│    - yield 전: 리소스 획득 (setup)          │
│    - yield 값: 엔드포인트에 주입            │
│    - yield 후: 리소스 정리 (teardown)       │
│    - 정리는 응답 전송 후 실행됨             │
│                                           │
│ 5. 같은 요청 내 동일 의존성은 캐싱          │
│    (매 요청마다 새로 생성, 요청 간 공유 없음) │
└───────────────────────────────────────────┘
```

**uvicorn의 동기 엔드포인트 처리:**
- FastAPI에서 `async def`가 아닌 일반 `def` 엔드포인트는 asyncio 이벤트 루프를 블로킹하지 않도록 `anyio.to_thread.run_sync()`를 통해 별도 스레드 풀(기본 40 스레드)에서 실행
- 이 때문에 psycopg2(동기 드라이버)를 사용해도 다른 요청을 동시에 처리할 수 있음
- 스레드 풀 크기는 `ThreadedConnectionPool`의 `maxconn`(10)과 독립적이므로, DB 커넥션 풀이 병목이 될 수 있음

### 4.6 API 엔드포인트 목록 (37개)

| 영역 | Method | URL | 기능 코드 |
|------|--------|-----|-----------|
| 인증 | POST | `/api/auth/login` | FN-001 |
| 인증 | POST | `/api/auth/register` | FN-002 |
| 인증 | GET | `/api/auth/permissions/{user_id}` | FN-003 |
| 품목 | POST | `/api/items` | FN-004 |
| 품목 | GET | `/api/items` | FN-005 |
| 품목 | GET | `/api/items/{item_code}` | FN-006 |
| 품목 | PUT | `/api/items/{item_code}` | FN-007 |
| BOM | POST | `/api/bom` | FN-008 |
| BOM | GET | `/api/bom` | FN-008 |
| BOM | GET | `/api/bom/summary` | FN-008 |
| BOM | GET | `/api/bom/where-used/{item_code}` | FN-009 |
| BOM | GET | `/api/bom/explode/{item_code}` | FN-009 |
| 공정 | GET | `/api/processes` | FN-010 |
| 공정 | POST | `/api/processes` | FN-010 |
| 라우팅 | GET | `/api/routings` | FN-011 |
| 라우팅 | POST | `/api/routings` | FN-011 |
| 라우팅 | GET | `/api/routings/{item_code}` | FN-012 |
| 설비 | POST | `/api/equipments` | FN-013 |
| 설비 | GET | `/api/equipments` | FN-014 |
| 설비 | PUT | `/api/equipments/{equip_code}/status` | FN-032 |
| 설비 | GET | `/api/equipments/status` | FN-033 |
| 계획 | POST | `/api/plans` | FN-015 |
| 계획 | GET | `/api/plans` | FN-016 |
| 계획 | GET | `/api/plans/{plan_id}` | FN-017 |
| AI | POST | `/api/ai/demand-forecast` | FN-018 |
| AI | GET | `/api/ai/demand-prediction/{item_code}` | FN-018 |
| AI | POST | `/api/ai/schedule-optimize` | FN-019 |
| 작업 | POST | `/api/work-orders` | FN-020 |
| 작업 | GET | `/api/work-orders` | FN-021 |
| 작업 | GET | `/api/work-orders/{wo_id}` | FN-022 |
| 실적 | POST | `/api/work-results` | FN-023 |
| 대시보드 | GET | `/api/dashboard/production` | FN-024 |
| 품질 | POST | `/api/quality/standards` | FN-025 |
| 품질 | POST | `/api/quality/inspections` | FN-026 |
| 품질 | GET | `/api/quality/defects` | FN-027 |
| AI | POST | `/api/ai/defect-predict` | FN-028 |
| AI | POST | `/api/ai/defect-prediction` | FN-028 |
| 재고 | POST | `/api/inventory/in` | FN-029 |
| 재고 | POST | `/api/inventory/out` | FN-030 |
| 재고 | GET | `/api/inventory` | FN-031 |
| AI | POST | `/api/ai/failure-predict` | FN-034 |
| 리포트 | GET | `/api/reports/production` | FN-035 |
| 리포트 | GET | `/api/reports/quality` | FN-036 |
| AI | POST | `/api/ai/insights` | FN-037 |
| 인프라 | GET | `/api/infra/status` | - |
| K8s | GET | `/api/k8s/pods` | - |
| K8s | GET | `/api/k8s/logs/{name}` | - |
| 네트워크 | GET | `/api/network/flows` | - |
| 네트워크 | GET | `/api/network/topology` | - |
| 네트워크 | GET | `/api/network/hubble-flows` | - |
| 네트워크 | GET | `/api/network/service-map` | - |

---

## 5. 프론트엔드 아키텍처

### 5.1 기술 구성

| 항목 | 기술 |
|------|------|
| 프레임워크 | React 19 |
| 번들러 | Vite (rolldown-vite 7.2.5) |
| CSS | Tailwind CSS 4 |
| HTTP 클라이언트 | Axios |
| 서빙 | nginx:alpine (K8s ConfigMap 마운트) |

### 5.2 단일 페이지 구조

전체 UI가 `App.jsx` 하나에 구현되어 있습니다 (약 1,200라인).

```
App.jsx
├── 공통 컴포넌트
│   ├── Card          — 통계 카드
│   ├── Table         — 데이터 테이블
│   ├── Badge         — 상태 뱃지
│   ├── Input         — 입력 필드
│   ├── Btn           — 버튼
│   ├── FilterBar     — 필터 바 컨테이너
│   ├── FilterSelect  — 드롭다운 필터
│   ├── FilterSearch  — 텍스트 검색
│   └── FilterCount   — 필터 카운트
│
├── 상태 관리
│   ├── menu          — 현재 메뉴 (14개 중 1개)
│   ├── db            — 코어 데이터 (items, flows, pods, infra)
│   ├── extra         — 페이지별 데이터
│   ├── tf            — 테이블 필터 상태
│   ├── bomTab        — BOM 서브탭 (list/explode/where)
│   ├── procTab       — Process 서브탭 (master/routing/summary)
│   ├── hubbleFilter  — 네트워크 필터 상태
│   └── serviceMap    — Hubble 서비스맵 데이터
│
└── 14개 메뉴 렌더링
    ├── DASHBOARD       — 요약 카드 4개
    ├── ITEMS           — 품목 테이블 + 필터
    ├── BOM             — 3탭 (목록/전개/역전개)
    ├── PROCESS         — 3탭 (마스터/라우팅뷰어/요약)
    ├── EQUIPMENT       — 설비 카드 그리드 + 필터
    ├── PLANS           — 생산계획 테이블 + 진행률
    ├── WORK_ORDER      — 작업지시 테이블 + 필터
    ├── QUALITY         — 불량 요약 + 트렌드 차트
    ├── INVENTORY       — 재고 테이블 + 필터
    ├── AI_CENTER       — 수요/불량/고장 예측 3칸
    ├── REPORTS         — 생산/품질 리포트 + AI 인사이트
    ├── NETWORK_FLOW    — Hubble 서비스맵 SVG + 플로우 테이블
    ├── INFRA_MONITOR   — CPU/메모리 게이지
    └── K8S_MANAGER     — Pod 목록 + 로그 뷰어
```

### 5.3 데이터 흐름

```
┌──────────┐   axios   ┌───────────────┐   proxy   ┌──────────┐
│ App.jsx  │──────────>│ nginx (:80)   │─────────>│ mes-api  │
│ React    │<──────────│ /api/* → :80  │<─────────│ FastAPI  │
└──────────┘   JSON    └───────────────┘          └──────────┘
     │
     ├── fetchCore(): 5초 간격 자동 새로고침 (대시보드, 인프라, Pod)
     ├── useEffect[menu]: 메뉴 변경 시 해당 데이터 로드
     └── useEffect[NETWORK_FLOW]: 5초 간격 Hubble 데이터 새로고침
```

### 5.4 nginx 프록시 설정

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;    # ConfigMap: frontend-build
        try_files $uri $uri/ /index.html;  # SPA 라우팅
    }

    location /api/ {
        proxy_pass http://mes-api-service:80;  # K8s Service
    }
}
```

프론트엔드에서 `/api/*` 요청은 nginx가 백엔드 서비스로 프록시합니다.
이를 통해 CORS 이슈 없이 같은 도메인에서 API를 호출할 수 있습니다.

---

## 6. 데이터베이스 스키마

### 6.1 ERD 개요

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  users   │     │  items   │────>│   bom    │ (parent/child)
└──────────┘     └────┬─────┘     └──────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
    ┌─────┴────┐ ┌────┴─────┐ ┌──┴───────────┐
    │processes │ │routings  │ │prod_plans    │
    └────┬─────┘ └──────────┘ └──────┬───────┘
         │                           │
    ┌────┴─────┐              ┌──────┴───────┐
    │equipments│              │ work_orders  │
    └──────────┘              └──────┬───────┘
                                     │
                              ┌──────┴───────┐
                              │ work_results │
                              └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  inventory   │  │ inspections  │  │  shipments   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 6.2 테이블 목록 (19개)

| 테이블 | PK | 설명 | 주요 컬럼 |
|--------|-----|------|-----------|
| `users` | user_id | 사용자 | password, name, role |
| `user_permissions` | user_id+menu | 권한 | can_read, can_write |
| `items` | item_code | 품목 | name, category, unit, spec, safety_stock |
| `bom` | bom_id | BOM | parent_item, child_item, qty_per_unit, loss_rate |
| `processes` | process_code | 공정 | name, std_time_min, equip_code |
| `routings` | routing_id | 라우팅 | item_code, seq, process_code, cycle_time |
| `equipments` | equip_code | 설비 | name, capacity_per_hour, status |
| `equip_status_log` | log_id | 설비 이력 | equip_code, status, reason, changed_at |
| `production_plans` | plan_id | 생산계획 | item_code, plan_qty, due_date, priority, status |
| `work_orders` | wo_id | 작업지시 | plan_id, item_code, work_date, equip_code |
| `work_results` | result_id | 작업실적 | wo_id, good_qty, defect_qty, worker_id |
| `quality_standards` | standard_id | 품질 기준 | item_code, check_name, min/max/std |
| `inspections` | inspection_id | 검사 | item_code, lot_no, judgment |
| `inspection_details` | detail_id | 검사 상세 | measured_value, judgment |
| `defect_codes` | defect_code | 불량 코드 | name, description |
| `inventory` | inv_id | 재고 | item_code, lot_no, qty, warehouse |
| `inventory_transactions` | tx_id | 재고 트랜잭션 | tx_type, qty, slip_no |
| `shipments` | shipment_id | 출하 | item_code, ship_date, qty |
| `defect_history` | defect_id | 불량 이력 | temperature, pressure, speed, humidity |
| `equip_sensors` | sensor_id | 센서 데이터 | vibration, temperature, current_amp |
| `ai_forecasts` | forecast_id | AI 예측 결과 | model_type, result_json |

### 6.3 시드 데이터

| 데이터 | 건수 |
|--------|------|
| 사용자 | 10명 (admin 1, manager 2, worker 5, viewer 2) |
| 품목 | 20건 (RAW 8, SEMI 6, PRODUCT 6) |
| BOM | 20건 |
| 공정 | 10건 |
| 라우팅 | 12개 품목 (36 공정 단계) |
| 설비 | 10대 |
| 생산계획 | 20건 |
| 작업지시 | 40건 |
| 작업실적 | 60건 |
| 재고 | 30건 |
| 출하 이력 | 24건 (12개월 x 2품목) |
| 불량 이력 | 8건 |

---

## 7. AI 모듈

### 7.1 수요 예측 (Demand Prediction)

- **알고리즘**: 선형 회귀 (Linear Regression)
- **데이터 소스**: `shipments` 테이블에서 월별 출하 집계
- **입력**: 품목 코드 (예: ITEM003)
- **출력**: 향후 3개월 예측 수량 + 신뢰도

### 7.2 불량 예측 (Defect Prediction)

- **알고리즘**: 통계 기반 임계값 비교
- **데이터 소스**: `defect_history` 테이블에서 정상 범위 통계
- **입력**: temperature, pressure, speed, humidity
- **출력**: 불량 확률(%), 주요 원인, 권장 조치

### 7.3 고장 예측 (Failure Prediction)

- **알고리즘**: 센서 데이터 기반 이상 감지
- **데이터 소스**: `equip_sensors` 테이블
- **입력**: 설비 코드, 진동/온도/전류 센서 값
- **출력**: 고장 확률(%), 잔여 수명(시간), 권장 조치

---

## 8. 네트워크 모니터링 (Hubble)

### 8.1 구성

```
Cilium Agent (DaemonSet)
    │
    ├── eBPF 프로그램 → 커널 레벨 패킷 관찰
    │
    └── Hubble Relay (Deployment)
            │
            └── gRPC API → k8s_service.py → /api/network/*
```

### 8.2 서비스맵

- **계층형 레이아웃**: External → Ingress → Application → Backend/Infra
- **고정 Y좌표**: 서비스 교차 최소화를 위한 수동 배치
- **포트 오프셋**: 같은 노드에서 여러 연결이 겹치지 않도록 분산
- **SVG 렌더링**: 브라우저 내 실시간 렌더링 (5초 새로고침)

### 8.3 표시 정보

- 서비스 노드: 이름, 네임스페이스, 프로토콜, 포트, 트래픽 카운트
- 연결선: 프로토콜, 포트, 전달/차단 수, 애니메이션
- 플로우 테이블: 타임스탬프, 소스/목적지, 판정, 프로토콜, L7 정보

---

## 9. 프로젝트 디렉터리 구조

```
MES_PROJECT/
├── app.py                        # FastAPI 메인 라우터 (37 endpoints)
├── requirements.txt              # Python 의존성
├── Dockerfile                    # 백엔드 Docker 이미지
├── docker-compose.yml            # 로컬 개발용 (PostgreSQL)
├── Jenkinsfile                   # CI/CD 파이프라인 (Jenkins)
├── init.sh                      # VM 부팅 후 원클릭 시작 (병렬 배포 + 프로그레스 바)
├── env.sh                        # 환경 변수 중앙 관리 + 프로그레스 바 유틸
├── setup-keycloak.sh             # Keycloak Realm/Client/사용자 자동 설정
│
├── api_modules/                  # 백엔드 비즈니스 로직 (27개 모듈)
│   ├── database.py               #   커넥션 풀
│   ├── mes_auth.py               #   인증
│   ├── mes_items.py              #   품목
│   ├── mes_bom.py                #   BOM
│   ├── mes_process.py            #   공정/라우팅
│   ├── mes_equipment.py          #   설비
│   ├── mes_plan.py               #   생산계획
│   ├── mes_work.py               #   작업지시/실적
│   ├── mes_quality.py            #   품질
│   ├── mes_inventory.py          #   재고
│   ├── mes_reports.py            #   리포트
│   ├── mes_ai_prediction.py      #   AI 수요예측
│   ├── mes_defect_predict.py     #   AI 불량예측
│   ├── k8s_service.py            #   K8s/Hubble API
│   ├── sys_logic.py              #   인프라 상태
│   └── ...                       #   기타 유틸리티 모듈
│
├── frontend/                     # React 프론트엔드
│   ├── src/
│   │   └── App.jsx               #   14메뉴 SPA (~1200 lines)
│   ├── package.json              #   npm 의존성
│   ├── vite.config.js            #   Vite 빌드 설정
│   ├── nginx.conf                #   프로덕션 nginx 설정
│   ├── .env.development          #   개발 환경변수
│   ├── .env.production           #   프로덕션 환경변수
│   └── dist/                     #   빌드 결과물
│
├── db/
│   └── init.sql                  # DB 스키마 + 시드 데이터 (19테이블, 500+건)
│
├── infra/                        # Kubernetes 매니페스트 (init.sh에서 참조)
│   ├── postgres-pv.yaml          #   PV + PVC
│   ├── db-secret.yaml            #   DB 접속 Secret
│   ├── postgres.yaml             #   PostgreSQL Deployment + Service
│   ├── keycloak.yaml             #   Keycloak Deployment + Service
│   ├── mes-api.yaml              #   FastAPI Deployment + Service
│   ├── nginx-config.yaml         #   nginx ConfigMap
│   └── mes-frontend.yaml         #   Frontend Deployment + Service
│
├── doc/                          # 문서
│   ├── HOWTOSTART.md             #   시작 가이드
│   ├── ARCH.md                   #   아키텍처 문서 (이 파일)
│   ├── HANDOVER.md               #   인수인계 문서
│   ├── HOWTOCONTRIBUTE.md        #   기여 가이드
│   ├── CODE_REVIEW.md            #   코드 품질 검토서
│   ├── CICD_REVIEW.md            #   CI/CD 파이프라인 검토서
│   ├── USER_MANUAL.md            #   사용자 매뉴얼
│   └── MES_PRESENTATION.md      #   Marp 발표 자료
│
└── README.md                     # 프로젝트 개요
```

---

## 10. 환경 변수

| 변수 | 기본값 | 사용처 |
|------|--------|--------|
| `DATABASE_URL` | `postgresql://postgres:mes1234@postgres:5432/mes_db` | 백엔드 → DB 연결 |
| `CORS_ORIGINS` | `http://<IP>:30173,http://localhost:30173,...` | 백엔드 CORS 허용 (env.sh에서 자동 생성) |
| `JWT_SECRET` | `mes-secret-key-2026` | 인증 토큰 서명 |
| `VITE_API_URL` | (비어있음 → nginx 프록시) | 프론트엔드 API 기본 URL |

---

## 11. 네트워크 포트 맵

```
외부 접근 (NodePort)
  :30173  ──→  mes-frontend-service  ──→  nginx:80
  :30461  ──→  mes-api-service       ──→  FastAPI:80

클러스터 내부 (ClusterIP)
  postgres:5432  ──→  PostgreSQL
  mes-api-service:80  ──→  FastAPI (nginx에서 프록시)
```

---

## 12. 기능 코드 매핑 (FN-001 ~ FN-037)

| FN | 기능 | 백엔드 모듈 | 프론트엔드 메뉴 |
|----|------|------------|----------------|
| FN-001~003 | 인증/권한 | mes_auth.py | - |
| FN-004~007 | 품목 관리 | mes_items.py | ITEMS |
| FN-008~009 | BOM 관리 | mes_bom.py | BOM |
| FN-010~012 | 공정/라우팅 | mes_process.py | PROCESS |
| FN-013~014 | 설비 관리 | mes_equipment.py | EQUIPMENT |
| FN-015~017 | 생산계획 | mes_plan.py | PLANS |
| FN-018~019 | AI 수요예측 | mes_ai_prediction.py | AI_CENTER |
| FN-020~024 | 작업지시/실적 | mes_work.py | WORK_ORDER |
| FN-025~027 | 품질관리 | mes_quality.py | QUALITY |
| FN-028 | AI 불량예측 | mes_defect_predict.py | AI_CENTER |
| FN-029~031 | 재고관리 | mes_inventory.py | INVENTORY |
| FN-032~034 | 설비 모니터링/AI | mes_equipment.py | AI_CENTER |
| FN-035~037 | 리포트/AI 인사이트 | mes_reports.py | REPORTS |

---

**최종 업데이트**: 2026-03-12
