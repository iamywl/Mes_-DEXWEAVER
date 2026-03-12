# KNU MES 시스템 — VM 부팅 후 시작 가이드

> VM(가상머신)을 켠 후 MES 시스템을 올리는 과정을 단계별로 설명합니다.

---

## 전제 조건

| 항목 | 값 |
|------|----|
| VM IP | `192.168.64.5` |
| OS | Ubuntu (aarch64) |
| 사용자 | `c1_master1` (sudo 권한) |
| 프로젝트 경로 | `/root/MES_PROJECT` |
| K8s 클러스터 | kubeadm 단일 노드 (c1master1) |

---

## 1단계: VM 접속

VM이 부팅된 후 SSH로 접속합니다.

```bash
# 외부 터미널에서
ssh c1_master1@192.168.64.5

# root 전환
sudo -s
# 비밀번호 입력
```

---

## 2단계: 원클릭 시작 스크립트 실행

```bash
bash /root/MES_PROJECT/init.sh
```

이 한 줄로 전체 시스템이 자동으로 올라갑니다.

---

## init.sh 가 수행하는 작업 (11단계, 최적화 버전)

> 모든 설정값은 `env.sh`에서 읽습니다 (하드코딩 없음).
> v5.4부터 병렬 배포, 빌드 캐시, 실시간 프로그레스 바가 적용되었습니다.

### 실시간 프로그레스 바

부팅 중 아래와 같은 프로그레스 바가 실시간으로 표시됩니다:

```
  [1:23] ████████████░░░░░░░░ 60%  ● ● ● ● ● ● ◉ ○ ○ ○ ○ 백엔드
```

- `[경과시간]` — 부팅 시작 후 경과 시간 (분:초)
- `█░` — 전체 진행률 바 (0~100%)
- `●` 완료 / `◉` 진행중 / `○` 대기 / `●`(빨강) 실패
- 마지막에 현재 진행 중인 단계 이름 표시

### 부팅 단계

| # | 단계 | 설명 | 최적화 |
|---|------|------|--------|
| 1 | 시스템설정 | swap off, containerd/kubelet 재시작 | - |
| 2 | K8s API | Kubernetes API 서버 응답 대기 (최대 60초) | - |
| 3 | 네트워크 | Cilium CNI 네트워크 복구 | 이미 Running이면 **스킵** |
| 4 | Pod정리 | Failed/Unknown/Error Pod 삭제 | - |
| 5 | DB배포 | PostgreSQL PV/PVC/Deployment 배포 | DB/Keycloak **병렬** apply |
| 6 | Keycloak | Keycloak 인증 서버 배포 | DB와 **동시** 배포 |
| 7 | 백엔드 | ConfigMap 생성 + FastAPI Deployment | pip **캐시** 재사용 (hostPath) |
| 8 | 프론트빌드 | React 빌드 | `dist/` 존재 + 소스 미변경 시 **빌드 스킵** |
| 9 | 프론트배포 | ConfigMap + nginx Deployment + rollout restart | - |
| 10 | 서비스대기 | 프론트/API/Keycloak HTTP 응답 확인 | 3개 서비스 **병렬** 대기 |
| 11 | KC설정 | Keycloak Realm/Client/사용자 자동 생성 | - |

---

### 각 단계별 내부 동작 메커니즘

#### 1단계: 시스템설정 — swap off, containerd/kubelet 재시작

```bash
swapoff -a
systemctl restart containerd
systemctl restart kubelet
```

##### swap off가 K8s에 필수인 이유

Kubernetes의 kubelet은 **cgroup 기반 리소스 제어**를 통해 각 Pod에 메모리 limit을 강제합니다. swap이 활성화되면 다음 문제가 발생합니다:

1. **QoS 보장 불가**: Pod에 `resources.limits.memory: 256Mi`를 설정해도, 커널이 초과 메모리를 swap으로 이동시키면 실제로는 256Mi 이상을 사용하게 됨
2. **OOM Killer 동작 왜곡**: kubelet은 메모리 부족 시 QoS class (Guaranteed > Burstable > BestEffort) 기반으로 Pod를 evict하는데, swap이 있으면 실제 메모리 압박 감지가 지연됨
3. **cgroup memory.limit_in_bytes 무력화**: cgroup v2에서 메모리 한도를 초과한 프로세스는 OOM Kill 대상이지만, swap 영역으로 페이지가 넘어가면 이 메커니즘이 정상 작동하지 않음

```
커널 메모리 관리 흐름 (swap이 있을 때의 문제):

Pod A (limit 256Mi)
  │
  ├─ 실제 RSS 사용: 300Mi (limit 초과!)
  │
  ├─ swap OFF: 즉시 OOM Kill → kubelet이 eviction 제어 가능 ✓
  │
  └─ swap ON:  커널이 44Mi를 swap으로 이동 → cgroup limit 회피
               → kubelet은 "정상"이라 판단 → QoS 보장 실패 ✗
```

> kubelet v1.22부터 `--fail-swap-on=true`가 기본값으로, swap이 켜져 있으면 kubelet 자체가 시작을 거부합니다.

##### containerd의 역할

containerd는 **OCI(Open Container Initiative) 호환 컨테이너 런타임**으로, kubelet과 컨테이너 사이의 중간 계층입니다:

```
┌─────────────────────────────────────────────────────┐
│                    kubelet                           │
│  (Pod 관리, 헬스체크, 리소스 모니터링)                  │
└───────────┬─────────────────────────────────────────┘
            │ CRI (Container Runtime Interface) gRPC
            ▼
┌─────────────────────────────────────────────────────┐
│                  containerd                          │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Image Store │ │ Snapshot Mgr │ │ Task Manager │  │
│  │ (이미지 풀/  │ │ (overlayfs   │ │ (컨테이너    │  │
│  │  캐시/저장)  │ │  레이어 관리) │ │  생명주기)   │  │
│  └─────────────┘ └──────────────┘ └──────┬───────┘  │
└──────────────────────────────────────────┼──────────┘
            │ OCI Runtime Spec                │
            ▼                                 ▼
┌─────────────────────┐           ┌────────────────┐
│       runc           │           │   shim v2      │
│ (실제 컨테이너 생성:  │           │ (프로세스 감시, │
│  namespace, cgroup,  │           │  stdio 관리)   │
│  pivot_root 호출)    │           └────────────────┘
└─────────────────────┘
```

containerd가 수행하는 핵심 동작:
- **Image Pull**: 레지스트리에서 OCI 이미지 다운로드 → content store에 blob 저장 → snapshotter로 레이어를 overlayfs로 합성
- **Container Create**: runc에 OCI runtime spec(config.json) 전달 → Linux namespace(pid, net, mnt, uts, ipc) + cgroup 생성 → pivot_root로 rootfs 전환
- **Container Lifecycle**: start → pause → resume → stop → delete 상태 전이 관리

##### kubelet 재시작 시 내부 동작

```
systemctl restart kubelet 실행 시 시퀀스:

  systemd                   kubelet                API Server         containerd
    │                         │                       │                   │
    ├─ SIGTERM 전송 ──────────►│                       │                   │
    │                         ├─ graceful shutdown     │                   │
    │                         ├─ watch 연결 종료 ──────►│                   │
    │                         ├─ PLEG 루프 중지         │                   │
    │                         │                       │                   │
    │  프로세스 종료 ◄──────────┤                       │                   │
    │                         │                       │                   │
    ├─ 새 프로세스 fork ───────►│                       │                   │
    │                         ├─ /var/lib/kubelet/     │                   │
    │                         │  config.yaml 로드      │                   │
    │                         │                       │                   │
    │                         ├─ CRI로 컨테이너 목록 ──────────────────────►│
    │                         │  조회 (ListContainers)  │                   │
    │                         │◄──────────────────── 기존 컨테이너 목록 ────┤
    │                         │                       │                   │
    │                         ├─ 기존 Pod와 컨테이너    │                   │
    │                         │  매핑 복구 (orphan 감지) │                   │
    │                         │                       │                   │
    │                         ├─ Node status 보고 ─────►│                   │
    │                         │  (capacity, conditions) │                   │
    │                         │                       ├─ etcd에 Node     │
    │                         │                       │  status 갱신      │
    │                         │                       │                   │
    │                         ├─ Pod watch 시작 ───────►│                   │
    │                         │  (assigned Pods 수신)   │                   │
    │                         │                       │                   │
    │                         ├─ PLEG 루프 재시작       │                   │
    │                         │  (Pod Lifecycle Event   │                   │
    │                         │   Generator: 1초 주기   │                   │
    │                         │   컨테이너 상태 폴링)    │                   │
    │                         │                       │                   │
```

핵심 포인트:
- kubelet이 재시작해도 **컨테이너는 죽지 않음** — containerd가 별도 프로세스로 컨테이너를 계속 관리
- kubelet은 CRI `ListContainers`/`ListPodSandbox`로 기존 컨테이너를 재발견하고, API Server에서 할당된 Pod 목록과 비교하여 상태를 복구
- **PLEG**(Pod Lifecycle Event Generator)가 재시작되어 1초 주기로 컨테이너 상태를 폴링하며, 변경 사항을 syncPod 루프에 전달

##### systemctl restart가 내부적으로 하는 일

```
systemctl restart kubelet
       │
       ▼
  systemd PID 1
       │
       ├─ 1. 해당 unit 파일 로드: /etc/systemd/system/kubelet.service
       │      [Service]
       │      ExecStart=/usr/bin/kubelet --config=/var/lib/kubelet/config.yaml ...
       │
       ├─ 2. 현재 MainPID에 SIGTERM 전송
       │      └─ TimeoutStopSec 후에도 살아있으면 SIGKILL
       │
       ├─ 3. cgroup /system.slice/kubelet.service 정리
       │      └─ 해당 cgroup의 모든 자식 프로세스 종료 확인
       │
       ├─ 4. ExecStart 명령으로 새 프로세스 fork + exec
       │      └─ 새 cgroup 할당, 리소스 제한 적용
       │
       └─ 5. Type=notify인 경우: sd_notify("READY=1") 수신 시 active 상태 전환
             Type=simple인 경우: fork 즉시 active 상태 전환
```

---

#### 2단계: K8s API 서버 응답 대기

```bash
# init.sh 내부 로직 (최대 60초 대기)
until kubectl get nodes &>/dev/null; do sleep 2; done
```

##### API Server 아키텍처

kube-apiserver는 K8s 클러스터의 **유일한 etcd 접근 게이트웨이**이자 **모든 컴포넌트 간 통신 허브**입니다:

```
                    ┌─────────────────────────────────────────────────┐
                    │              kube-apiserver                      │
                    │                                                 │
  kubectl ─────────►│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
  (REST API)        │  │ AuthN     │  │ AuthZ      │  │ Admission │  │
                    │  │           │  │            │  │ Controller│  │
                    │  │• x509 cert│  │• RBAC      │  │           │  │
                    │  │• Bearer   │  │• Node      │  │• Mutating │  │
                    │  │  Token    │  │  Authorizer│  │• Validating│  │
                    │  │• Bootstrap│  │            │  │• Webhook  │  │
                    │  │  Token    │  │            │  │           │  │
                    │  └─────┬─────┘  └─────┬──────┘  └─────┬─────┘  │
                    │        │              │               │         │
                    │        ▼              ▼               ▼         │
                    │  ┌──────────────────────────────────────────┐   │
                    │  │         API Handler (REST)                │   │
                    │  │  • Resource CRUD → etcd read/write       │   │
                    │  │  • Watch → etcd watcher 변환             │   │
                    │  │  • List → etcd range query               │   │
                    │  └──────────────────┬───────────────────────┘   │
                    └─────────────────────┼───────────────────────────┘
                                          │ gRPC
                                          ▼
                                    ┌───────────┐
                                    │   etcd    │
                                    │ (key-value│
                                    │  store)   │
                                    └───────────┘
```

##### `kubectl get nodes` 실행 시 내부 과정

```
kubectl                  kube-apiserver              etcd
  │                           │                        │
  ├─ 1. ~/.kube/config 로드    │                        │
  │    (cluster CA, client     │                        │
  │     cert, server URL)      │                        │
  │                           │                        │
  ├─ 2. TLS Handshake ───────►│                        │
  │    ClientHello             │                        │
  │    (SNI: kubernetes)       │                        │
  │◄── ServerHello ───────────┤                        │
  │    (서버 인증서 전송)        │                        │
  │    (클라이언트 인증서 요청)   │                        │
  ├── 클라이언트 인증서 전송 ──►│                        │
  │                           │                        │
  ├─ 3. HTTP Request ────────►│                        │
  │    GET /api/v1/nodes       │                        │
  │    Authorization: Bearer   │                        │
  │    <token>                 │                        │
  │                           │                        │
  │                           ├─ 4. AuthN: 인증서/토큰   │
  │                           │    에서 사용자 식별       │
  │                           │    → system:admin        │
  │                           │                        │
  │                           ├─ 5. AuthZ: RBAC 확인     │
  │                           │    ClusterRole 조회      │
  │                           │    → nodes GET 허용?     │
  │                           │                        │
  │                           ├─ 6. Admission: 읽기는    │
  │                           │    admission 미적용      │
  │                           │                        │
  │                           ├─ 7. etcd 조회 ──────────►│
  │                           │    Range: /registry/     │
  │                           │    minions/              │
  │                           │◄──── 노드 목록 반환 ──────┤
  │                           │                        │
  │◄── 8. HTTP 200 ──────────┤                        │
  │    JSON: {kind: NodeList,  │                        │
  │     items: [{name:         │                        │
  │      c1master1, ...}]}     │                        │
  │                           │                        │
```

##### API Server가 ready 되려면 필요한 조건

1. **etcd 연결 성공**: apiserver → etcd gRPC 연결이 수립되어야 함. etcd가 아직 leader election 중이면 apiserver는 대기
2. **TLS 인증서 로드**: `/etc/kubernetes/pki/` 하위의 apiserver.crt, apiserver.key, ca.crt 등이 유효해야 함
3. **Admission Controller 초기화**: MutatingAdmissionWebhook, ValidatingAdmissionWebhook 등이 로드 완료
4. **/healthz 엔드포인트 응답**: 내부적으로 etcd health, RBAC readiness, informer sync 여부를 종합 판단
5. **kube-apiserver Static Pod 실행**: kubelet이 `/etc/kubernetes/manifests/kube-apiserver.yaml`을 읽어 컨테이너를 실행해야 함

---

#### 3단계: Cilium CNI 네트워크 복구

##### Cilium DaemonSet이 각 노드에서 하는 일

Cilium은 전통적인 iptables 대신 **Linux 커널의 eBPF(extended Berkeley Packet Filter)**를 활용하여 네트워크 정책과 라우팅을 수행합니다:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Linux Kernel                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    eBPF Subsystem                        │    │
│  │                                                         │    │
│  │  TC (Traffic Control) hook:                              │    │
│  │    ingress ──► eBPF prog ──► 패킷 허용/차단/리다이렉트   │    │
│  │    egress  ──► eBPF prog ──► 패킷 허용/차단/리다이렉트   │    │
│  │                                                         │    │
│  │  XDP (eXpress Data Path) hook:                          │    │
│  │    NIC 드라이버 ──► eBPF prog ──► 초고속 패킷 처리       │    │
│  │                                                         │    │
│  │  eBPF Maps (커널 메모리 내 key-value 해시 테이블):        │    │
│  │    ┌──────────────────┐  ┌──────────────────────────┐   │    │
│  │    │ Endpoint Map     │  │ CT (Connection Tracking) │   │    │
│  │    │ PodIP → identity │  │ Map: 5-tuple → connstate │   │    │
│  │    └──────────────────┘  └──────────────────────────┘   │    │
│  │    ┌──────────────────┐  ┌──────────────────────────┐   │    │
│  │    │ Policy Map       │  │ NAT Map                  │   │    │
│  │    │ identity×port →  │  │ ServiceIP:port →         │   │    │
│  │    │ allow/deny       │  │ BackendPodIP:port        │   │    │
│  │    └──────────────────┘  └──────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ veth pair│  │ veth pair│  │ veth pair│  ← Pod 네트워크       │
│  │ (Pod A)  │  │ (Pod B)  │  │ (Pod C)  │    인터페이스         │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

Cilium Agent(DaemonSet Pod) 시작 시 수행하는 작업:

1. **eBPF 프로그램 컴파일/로드**: Cilium은 C로 작성된 eBPF 프로그램을 LLVM으로 컴파일 → `bpf()` syscall로 커널에 로드
2. **Endpoint 맵 생성**: 각 Pod의 veth 인터페이스를 스캔하여 `{PodIP → Security Identity}` 맵 구성
3. **TC hook 부착**: 각 veth pair의 ingress/egress에 eBPF 프로그램을 부착 (`tc filter add dev ... bpf`)
4. **CiliumNode CRD 등록**: 자신의 노드 CIDR, health IP 등을 Custom Resource로 API Server에 등록

##### 네트워크 복구 시 eBPF 맵 재구성 과정

VM 재시작 후 Cilium Pod가 재생성되면:

```
Cilium Agent (Pod)           Linux Kernel              API Server
      │                         │                         │
      ├─ 1. 기존 eBPF 맵 탐색    │                         │
      │    (/sys/fs/bpf/tc/     │                         │
      │     globals/)            │                         │
      │    → VM 재시작으로        │                         │
      │      맵이 사라진 상태     │                         │
      │                         │                         │
      ├─ 2. CiliumEndpoint ─────────────────────────────►│
      │    CR 목록 조회           │                         │
      │◄──────────────────── endpoint 목록 반환 ───────────┤
      │                         │                         │
      ├─ 3. 새 eBPF 맵 생성 ────►│                         │
      │    bpf(BPF_MAP_CREATE,   │                         │
      │     BPF_MAP_TYPE_HASH)   │                         │
      │                         │                         │
      ├─ 4. Endpoint 맵 채우기 ──►│                         │
      │    bpf(BPF_MAP_UPDATE)   │                         │
      │    각 Pod IP → identity  │                         │
      │                         │                         │
      ├─ 5. eBPF 프로그램 로드 ──►│                         │
      │    bpf(BPF_PROG_LOAD,    │                         │
      │     BPF_PROG_TYPE_SCHED  │                         │
      │     _CLS)                │                         │
      │                         │                         │
      ├─ 6. TC hook에 부착 ─────►│                         │
      │    tc filter add dev     │                         │
      │    lxc_xxx bpf ...       │                         │
      │                         │                         │
      ├─ 7. cilium status 보고 ──────────────────────────►│
      │    CiliumNode Ready      │                         │
      │                         │                         │
```

##### Pod 간 통신 가능 조건

Pod 간 통신이 정상적으로 이루어지려면 다음이 모두 충족되어야 합니다:

1. **Cilium Agent가 Running 상태**: eBPF 프로그램이 커널에 로드되어 있어야 함
2. **Endpoint 맵 완성**: 모든 Pod의 veth 인터페이스에 대한 identity 매핑이 완료
3. **IPAM 할당 완료**: 각 Pod에 클러스터 CIDR 내의 IP가 할당됨
4. **veth pair 생성**: Pod sandbox 생성 시 CNI가 호스트-Pod 간 veth pair를 생성해야 함
5. **ARP/Neighbor 테이블 갱신**: 같은 노드의 Pod 간에는 L2 forwarding, 다른 노드면 VXLAN/Geneve 터널 또는 direct routing

---

#### 4단계: Pod 정리 — Failed/Unknown/Error Pod 삭제

```bash
kubectl delete pod --field-selector=status.phase==Failed --all-namespaces
```

##### kubectl delete pod 실행 시 내부 흐름

```
kubectl                API Server           etcd          kubelet         containerd
  │                       │                  │               │               │
  ├─ DELETE /api/v1/     │                  │               │               │
  │  namespaces/xx/pods/ │                  │               │               │
  │  <pod-name>          │                  │               │               │
  │  ──────────────────►│                  │               │               │
  │                      │                  │               │               │
  │                      ├─ Pod 객체에       │               │               │
  │                      │  deletionTimestamp│               │               │
  │                      │  + deletionGrace  │               │               │
  │                      │  PeriodSeconds    │               │               │
  │                      │  설정 후 etcd 저장 ►│               │               │
  │                      │                  │               │               │
  │                      │                  │  watch event   │               │
  │                      │  Pod MODIFIED ────────────────►│               │
  │                      │  (deletionTimestamp 존재)       │               │
  │                      │                  │               │               │
  │                      │                  │               ├─ Graceful     │
  │                      │                  │               │  Shutdown 시작 │
  │                      │                  │               │               │
  │                      │                  │               ├─ preStop hook │
  │                      │                  │               │  실행 (있으면)  │
  │                      │                  │               │               │
  │                      │                  │               ├─ SIGTERM ─────►│
  │                      │                  │               │  전송          │ → 컨테이너
  │                      │                  │               │               │   프로세스에
  │                      │                  │               │               │   전달
  │                      │                  │               │               │
  │                      │                  │      (gracePeriod 대기, 기본 30초)
  │                      │                  │               │               │
  │                      │                  │               ├─ SIGKILL ─────►│
  │                      │                  │               │  (타임아웃 시)  │ → 강제 종료
  │                      │                  │               │               │
  │                      │                  │               ├─ API Server에  │
  │                      │                  │               │  상태 보고 ─────┤
  │                      │                  │               │               │
  │                      ├─ etcd에서 Pod ───►│               │               │
  │                      │  객체 최종 삭제    │               │               │
  │                      │                  │               │               │
  │◄── 200 OK ──────────┤                  │               │               │
  │                      │                  │               │               │
```

##### Failed/Unknown/Error 상태 발생 원인

| 상태 | 발생 원인 | 상세 |
|------|-----------|------|
| **Failed** | 컨테이너가 비정상 종료 (exit code != 0), restartPolicy=Never인 경우 재시작 안 됨. Init 컨테이너 실패 시에도 발생 |
| **Unknown** | kubelet이 API Server에 node status를 보고하지 못함 (node가 다운되거나 네트워크 단절). NodeController가 `node.kubernetes.io/unreachable` taint를 추가하고 Pod 상태를 Unknown으로 변경 |
| **Error** | CrashLoopBackOff의 일종으로, Pod spec 자체에 오류가 있거나 (잘못된 이미지, 없는 ConfigMap 참조 등) kubelet이 sandbox 생성에 실패한 경우 |

VM 재시작 후 이 상태의 Pod가 남아있는 이유: 이전 실행에서 정상 종료되지 못한 Pod 객체가 etcd에 남아있기 때문입니다.

---

#### 5~6단계: DB/Keycloak 배포

```bash
# 병렬 실행
kubectl apply -f infra/postgres-pv.yaml -f infra/db-secret.yaml -f infra/postgres.yaml &
kubectl apply -f infra/keycloak.yaml &
wait
```

##### kubectl apply 실행 시 내부 흐름

```
  YAML 파일            kubectl              API Server        Controller       Scheduler       kubelet
     │                   │                     │              Manager            │               │
     │   파싱/검증        │                     │                │                │               │
     ├──────────────────►│                     │                │                │               │
     │                   │                     │                │                │               │
     │                   ├─ 1. YAML → JSON 변환 │                │                │               │
     │                   │    + API 버전 확인    │                │                │               │
     │                   │                     │                │                │               │
     │                   ├─ 2. POST/PATCH ─────►│                │                │               │
     │                   │    /apis/apps/v1/    │                │                │               │
     │                   │    deployments       │                │                │               │
     │                   │                     │                │                │               │
     │                   │                     ├─ 3. AuthN/AuthZ│                │               │
     │                   │                     │    인증/인가 검사│                │               │
     │                   │                     │                │                │               │
     │                   │                     ├─ 4. Admission  │                │               │
     │                   │                     │ a) Mutating:    │                │               │
     │                   │                     │    defaulting,  │                │               │
     │                   │                     │    sidecar 주입  │                │               │
     │                   │                     │ b) Validating:  │                │               │
     │                   │                     │    스키마 검증,   │                │               │
     │                   │                     │    정책 검사      │                │               │
     │                   │                     │                │                │               │
     │                   │                     ├─ 5. etcd 저장   │                │               │
     │                   │                     │    /registry/   │                │               │
     │                   │                     │    deployments/ │                │               │
     │                   │                     │    ns/name      │                │               │
     │                   │                     │                │                │               │
     │                   │                     │ watch event ──►│                │               │
     │                   │                     │                │                │               │
     │                   │                     │                ├─ 6. Deployment │               │
     │                   │                     │                │  Controller:    │               │
     │                   │                     │                │  ReplicaSet 생성│               │
     │                   │                     │                │                │               │
     │                   │                     │                ├─ 7. ReplicaSet │               │
     │                   │                     │                │  Controller:    │               │
     │                   │                     │                │  Pod 객체 생성   │               │
     │                   │                     │                │                │               │
     │                   │                     │  Pod 객체 감지 ────────────────►│               │
     │                   │                     │  (nodeName 미지정)              │               │
     │                   │                     │                │                │               │
     │                   │                     │                │   8. Scheduler: │               │
     │                   │                     │                │   filtering →   │               │
     │                   │                     │                │   scoring →     │               │
     │                   │                     │                │   binding       │               │
     │                   │                     │                │   (nodeName 설정)│               │
     │                   │                     │                │                │               │
     │                   │                     │  Pod binding event ────────────────────────────►│
     │                   │                     │                │                │               │
     │                   │                     │                │                │  9. kubelet:   │
     │                   │                     │                │                │  - sandbox 생성│
     │                   │                     │                │                │  - image pull  │
     │                   │                     │                │                │  - container   │
     │                   │                     │                │                │    start       │
     │                   │                     │                │                │  - volume mount│
```

##### PersistentVolume이 Pod에 바인딩되는 과정

```
PV/PVC/Pod 바인딩 시퀀스:

  관리자 (YAML)        API Server        PV Controller       Scheduler        kubelet
      │                   │                  │                   │               │
      ├─ PV 생성 ────────►│                  │                   │               │
      │  (hostPath:       │── etcd 저장      │                   │               │
      │   /data/postgres) │                  │                   │               │
      │                   │                  │                   │               │
      ├─ PVC 생성 ───────►│                  │                   │               │
      │  (요청: 1Gi)      │── etcd 저장      │                   │               │
      │                   │                  │                   │               │
      │                   │  watch event ──►│                   │               │
      │                   │                  │                   │               │
      │                   │                  ├─ PVC-PV 매칭:     │               │
      │                   │                  │  capacity >= 요청  │               │
      │                   │                  │  accessMode 일치   │               │
      │                   │                  │  storageClass 일치 │               │
      │                   │                  │                   │               │
      │                   │◄── Bind 요청 ────┤                   │               │
      │                   │  PV.claimRef =   │                   │               │
      │                   │  PVC             │                   │               │
      │                   │  PVC.volumeName = │                   │               │
      │                   │  PV              │                   │               │
      │                   │                  │                   │               │
      │  Pod 생성 ────────►│                  │                   │               │
      │  (volumeMounts:   │                  │                   │               │
      │   claimName: xxx) │                  │                   │               │
      │                   │                  │                   │               │
      │                   │──── Pod 스케줄링 ───────────────────►│               │
      │                   │                  │                   │               │
      │                   │                  │         노드에 바인딩 ───────────►│
      │                   │                  │                   │               │
      │                   │                  │                   │  Volume Mount: │
      │                   │                  │                   │  hostPath의 경우│
      │                   │                  │                   │  mount --bind  │
      │                   │                  │                   │  /data/postgres│
      │                   │                  │                   │  → 컨테이너     │
      │                   │                  │                   │    /var/lib/   │
      │                   │                  │                   │    postgresql  │
      │                   │                  │                   │               │
```

##### PostgreSQL 컨테이너 시작 시 initdb 프로세스 동작

PostgreSQL 공식 이미지(`postgres:15`)의 entrypoint가 수행하는 작업:

```
docker-entrypoint.sh 실행 흐름:

  1. PGDATA 디렉토리 확인 (/var/lib/postgresql/data)
     │
     ├─ PGDATA가 비어있는 경우 (최초 실행):
     │   │
     │   ├─ initdb 실행:
     │   │   ├─ WAL(Write-Ahead Log) 디렉토리 생성
     │   │   ├─ pg_hba.conf 생성 (접근 제어)
     │   │   ├─ postgresql.conf 생성 (서버 설정)
     │   │   ├─ 시스템 카탈로그 테이블 생성
     │   │   └─ template0, template1 DB 초기화
     │   │
     │   ├─ 임시 서버 시작 (unix socket only)
     │   │
     │   ├─ /docker-entrypoint-initdb.d/ 스캔:
     │   │   ├─ *.sql   → psql로 실행
     │   │   ├─ *.sql.gz → gunzip | psql
     │   │   └─ *.sh    → bash로 실행
     │   │   (여기서 init.sql이 실행되어 21개 테이블 + 시드 데이터 생성)
     │   │
     │   └─ 임시 서버 종료
     │
     └─ PGDATA에 데이터가 있는 경우 (PV에 기존 데이터 존재):
         └─ initdb 스킵 → 바로 서버 시작

  2. PostgreSQL 메인 서버 시작:
     └─ postgres -D $PGDATA
        ├─ shared memory 할당 (shared_buffers)
        ├─ WAL writer 프로세스 시작
        ├─ checkpoint 프로세스 시작
        ├─ autovacuum launcher 시작
        ├─ stats collector 시작
        └─ TCP 5432 포트 리스닝 대기
```

---

#### 7단계: 백엔드 배포

```bash
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/
kubectl apply -f infra/mes-api.yaml
```

##### ConfigMap 생성의 내부 동작

```bash
kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/
```

이 명령이 실행되면:

1. **파일 읽기**: kubectl이 로컬 파일 시스템에서 `app.py`와 `api_modules/` 하위 파일들을 읽음
2. **JSON 변환**: 파일 내용을 ConfigMap 객체의 `data` 필드에 key-value로 매핑
   - key = 파일명 (예: `app.py`, `database.py`)
   - value = 파일 내용 (텍스트 그대로, base64 인코딩은 `binaryData`일 때만)
3. **API Server 전송**: `POST /api/v1/namespaces/default/configmaps` → etcd에 저장

> 주의: ConfigMap의 크기 제한은 **1MiB** (etcd의 단일 value 크기 제한). 코드 파일 전체를 담아야 하므로 이 제한에 유의해야 합니다.

##### Pod 시작 시 ConfigMap 마운트에서 uvicorn 시작까지

```
kubelet이 Pod를 시작할 때의 전체 시퀀스:

  kubelet               containerd/runc          컨테이너 프로세스
    │                        │                        │
    ├─ 1. Sandbox 생성       │                        │
    │    (pause 컨테이너:     │                        │
    │     네트워크 NS 확보)   │                        │
    │                        │                        │
    ├─ 2. CNI 호출 ──────────────► Cilium:             │
    │    (veth pair 생성,         Pod IP 할당,          │
    │     IP 할당)                eBPF endpoint 등록    │
    │                        │                        │
    ├─ 3. Volume 준비        │                        │
    │  a) ConfigMap Volume:  │                        │
    │     API Server에서     │                        │
    │     ConfigMap 데이터    │                        │
    │     조회               │                        │
    │     → /var/lib/kubelet/│                        │
    │       pods/<uid>/      │                        │
    │       volumes/         │                        │
    │       kubernetes.io~   │                        │
    │       configmap/       │                        │
    │       api-code/        │                        │
    │       에 파일 생성       │                        │
    │     (실제로는 tmpfs에    │                        │
    │      symlink 구조)      │                        │
    │                        │                        │
    │  b) hostPath Volume:   │                        │
    │     /root/pip-cache →  │                        │
    │     컨테이너 내부에      │                        │
    │     bind mount         │                        │
    │                        │                        │
    ├─ 4. Image Pull ───────►│                        │
    │    (python:3.9-slim    │                        │
    │     이미지 레이어 확인   │                        │
    │     → 캐시에 있으면     │                        │
    │       pull 스킵)       │                        │
    │                        │                        │
    ├─ 5. Container Create ─►│                        │
    │    OCI spec 전달:       │                        │
    │    - rootfs            │                        │
    │    - mounts (ConfigMap │                        │
    │      + hostPath)       │                        │
    │    - env vars          │                        │
    │                        ├─ runc create:          │
    │                        │  clone(CLONE_NEWPID|   │
    │                        │   CLONE_NEWNS|         │
    │                        │   CLONE_NEWNET...)      │
    │                        │  → cgroup 설정          │
    │                        │  → mount namespace      │
    │                        │    구성                  │
    │                        │  → pivot_root           │
    │                        │                        │
    ├─ 6. Container Start ──►│────────────────────────►│
    │                        │                        │
    │                        │                        ├─ entrypoint 실행:
    │                        │                        │  (mes-api.yaml의 command)
    │                        │                        │
    │                        │                        ├─ cp /code/*.py /app/
    │                        │                        │  (ConfigMap → 작업 디렉토리)
    │                        │                        │
    │                        │                        ├─ pip install -r
    │                        │                        │  requirements.txt
    │                        │                        │  --cache-dir=/pip-cache
    │                        │                        │  (hostPath 캐시 활용)
    │                        │                        │
    │                        │                        └─ uvicorn app:app
    │                        │                           --host 0.0.0.0
    │                        │                           --port 8000
```

##### uvicorn이 ASGI 앱을 로드하는 과정

```
uvicorn app:app --host 0.0.0.0 --port 8000 실행 시:

  uvicorn (메인 프로세스)
    │
    ├─ 1. 모듈 임포트: importlib.import_module("app")
    │      → app.py 실행
    │      → FastAPI() 인스턴스 생성
    │      → 모든 @app.get/post 데코레이터 실행하여 라우트 테이블 구축
    │      → api_modules/ 하위 모듈 import
    │
    ├─ 2. ASGI 앱 객체 확인: app.app (FastAPI 인스턴스)
    │      → ASGIApplication 프로토콜 구현 확인
    │        (async def __call__(scope, receive, send))
    │
    ├─ 3. uvloop 또는 asyncio 이벤트 루프 생성
    │
    ├─ 4. TCP 소켓 바인딩:
    │      socket() → bind(0.0.0.0:8000) → listen(backlog=2048)
    │
    ├─ 5. lifespan 이벤트 발생:
    │      → ASGI lifespan.startup 이벤트 전송
    │      → FastAPI의 @app.on_event("startup") 핸들러 실행
    │
    └─ 6. 요청 수신 대기 (이벤트 루프):
         accept() → 각 연결마다:
           ├─ HTTP/1.1 파싱 (h11 라이브러리)
           ├─ ASGI scope 생성 (type, path, method, headers)
           ├─ FastAPI 라우터에 dispatch
           │    → path matching → dependency injection → handler 실행
           └─ ASGI send로 응답 전송
```

---

#### 8~9단계: 프론트엔드 빌드/배포

##### Vite 빌드 과정 (npm run build)

```bash
cd /root/MES_PROJECT/frontend && npm run build
# 실제 실행: vite build
```

```
Vite 빌드 파이프라인:

  vite build 실행
    │
    ├─ 1. vite.config.js 로드
    │      → plugins, build 옵션, resolve 설정 파싱
    │
    ├─ 2. 엔트리 포인트 분석: src/main.jsx
    │      → import 트리 순회 (의존성 그래프 구축)
    │
    ├─ 3. ESBuild 변환 (개별 파일 수준):
    │      ├─ JSX → JavaScript 변환 (React.createElement 호출로)
    │      ├─ TypeScript → JavaScript (해당시)
    │      └─ ESBuild는 Go로 작성 → 매우 빠른 변환 속도
    │
    ├─ 4. Rollup 번들링 (모듈 결합):
    │      ├─ Tree Shaking:
    │      │    ES Module의 static import/export 분석
    │      │    → 사용되지 않는 export 제거
    │      │    → Dead code elimination
    │      │
    │      ├─ Code Splitting:
    │      │    dynamic import() 기준으로 청크 분리
    │      │    → vendor 라이브러리 별도 청크
    │      │    → lazy-loaded 컴포넌트 별도 청크
    │      │
    │      ├─ Asset Processing:
    │      │    CSS → PostCSS → Tailwind JIT 컴파일
    │      │    → 사용된 유틸리티 클래스만 추출
    │      │    → minification (cssnano)
    │      │
    │      └─ Minification:
    │           terser 또는 esbuild로 JS 최소화
    │           → 변수명 단축, 공백 제거, 상수 접기
    │
    └─ 5. 출력: dist/
         ├─ index.html          (엔트리 HTML, 해시된 JS/CSS 참조)
         ├─ assets/
         │   ├─ index-[hash].js  (메인 번들)
         │   ├─ vendor-[hash].js (React, 라이브러리)
         │   └─ index-[hash].css (Tailwind CSS)
         └─ (기타 정적 자산)
```

##### nginx가 정적 파일을 서빙하는 원리

```
클라이언트 브라우저                    nginx (Pod)
      │                                 │
      ├─ GET /index.html ──────────────►│
      │                                 │
      │                                 ├─ Event-driven I/O:
      │                                 │    nginx는 worker 프로세스가
      │                                 │    epoll(Linux)/kqueue(macOS)로
      │                                 │    수천 개 연결을 비동기 처리
      │                                 │    (스레드 1개당 수만 연결 가능)
      │                                 │
      │                                 ├─ 파일 위치 결정:
      │                                 │    root /usr/share/nginx/html;
      │                                 │    → /usr/share/nginx/html/index.html
      │                                 │
      │                                 ├─ sendfile() syscall:
      │                                 │    커널이 디스크 → 소켓으로 직접 전송
      │                                 │    (userspace 복사 없이 zero-copy)
      │                                 │
      │                                 │    일반적 방식:
      │                                 │      disk → kernel buf → user buf
      │                                 │      → kernel buf → NIC
      │                                 │
      │                                 │    sendfile 방식:
      │                                 │      disk → kernel buf → NIC
      │                                 │      (2번의 복사 절약)
      │                                 │
      │◄── HTTP 200 + 파일 내용 ─────────┤
      │    Content-Type: text/html       │
      │    Content-Encoding: gzip        │
      │    (gzip on; 설정 시 실시간 압축)  │
      │                                 │
```

##### nginx 리버스 프록시의 /api/* 요청 처리 흐름

```
브라우저              nginx (frontend Pod)           mes-api Service          API Pod
   │                       │                              │                     │
   ├─ GET /api/items ─────►│                              │                     │
   │                       │                              │                     │
   │                       ├─ location /api/ 매칭          │                     │
   │                       │  → proxy_pass 설정 확인       │                     │
   │                       │    proxy_pass                 │                     │
   │                       │    http://mes-api-svc:8000;   │                     │
   │                       │                              │                     │
   │                       ├─ DNS 조회:                    │                     │
   │                       │  mes-api-svc →                │                     │
   │                       │  CoreDNS가 ClusterIP 반환     │                     │
   │                       │  (예: 10.96.x.x)              │                     │
   │                       │                              │                     │
   │                       ├─ upstream TCP 연결 ──────────►│                     │
   │                       │  (keep-alive로 연결 재사용     │                     │
   │                       │   가능: upstream keepalive     │                     │
   │                       │   설정에 따라)                 │                     │
   │                       │                              │                     │
   │                       │                              ├─ iptables/eBPF     │
   │                       │                              │  DNAT:              │
   │                       │                              │  ClusterIP:8000 →   │
   │                       │                              │  PodIP:8000         │
   │                       │                              │                     │
   │                       │                              ├─────────────────────►│
   │                       │                              │                     │
   │                       │                              │◄── JSON 응답 ────────┤
   │                       │◄── 프록시 응답 ──────────────┤                     │
   │                       │                              │                     │
   │                       ├─ 헤더 조작:                   │                     │
   │                       │  X-Real-IP, X-Forwarded-For   │                     │
   │                       │  추가                         │                     │
   │                       │                              │                     │
   │◄── HTTP 200 JSON ────┤                              │                     │
   │                       │                              │                     │
```

nginx의 TCP 연결 재사용 (keep-alive):
- 매 API 요청마다 3-way handshake를 반복하면 지연이 발생
- `upstream` 블록에서 `keepalive 32;` 설정 시, nginx가 backend와의 TCP 연결을 풀(pool)로 유지
- 후속 요청은 기존 연결을 재활용하여 handshake 비용 절감

---

#### 10단계: 서비스 대기 — Health Check

```bash
# 3개 서비스 병렬 대기
curl -sf http://localhost:30173 &>/dev/null &   # 프론트엔드
curl -sf http://localhost:30461/api/health &     # API
curl -sf http://localhost:30080 &                # Keycloak
wait
```

##### K8s Service의 트래픽 라우팅 원리

```
외부 요청                  Node                    kube-proxy/Cilium         Pod
   │                       │                           │                     │
   ├─ http://NodeIP:30173 ►│                           │                     │
   │                       │                           │                     │
   │                       ├─ NodePort 수신:            │                     │
   │                       │  커널 소켓이 30173         │                     │
   │                       │  포트에서 리스닝            │                     │
   │                       │                           │                     │
   │                       │                           │                     │
   │                   [iptables 모드의 경우]            │                     │
   │                       │                           │                     │
   │                       ├─ PREROUTING chain:         │                     │
   │                       │  KUBE-SERVICES →           │                     │
   │                       │  KUBE-NODEPORTS →          │                     │
   │                       │  KUBE-SVC-XXXX (Service) → │                     │
   │                       │  KUBE-SEP-YYYY (Endpoint)  │                     │
   │                       │                           │                     │
   │                       ├─ DNAT 규칙 적용:           │                     │
   │                       │  dst: NodeIP:30173 →       │                     │
   │                       │  dst: PodIP:80             │                     │
   │                       │                           │                     │
   │                   [Cilium eBPF 모드의 경우]         │                     │
   │                       │                           │                     │
   │                       ├─ eBPF 프로그램이 ──────────►│                     │
   │                       │  소켓 레벨에서 가로챔       │                     │
   │                       │                           ├─ Service Map 조회:  │
   │                       │                           │  NodePort 30173 →   │
   │                       │                           │  ClusterIP:port     │
   │                       │                           │                     │
   │                       │                           ├─ Endpoint Map 조회: │
   │                       │                           │  ClusterIP:port →   │
   │                       │                           │  [PodIP1, PodIP2]   │
   │                       │                           │  → 선택 (라운드로빈  │
   │                       │                           │    또는 Maglev 해싱) │
   │                       │                           │                     │
   │                       │                           ├─ 패킷 헤더 직접 수정 │
   │                       │                           │  (iptables 우회,     │
   │                       │                           │   conntrack 불필요)  │
   │                       │                           │                     │
   │                       │  ◄─── 패킷 전달 ──────────┼─────────────────────►│
   │                       │                           │                     │
   │◄── HTTP 응답 ─────────┤                           │                     │
   │                       │                           │                     │
```

Cilium eBPF 모드가 iptables보다 효율적인 이유:
- iptables는 규칙이 선형 리스트 → Service/Pod 수가 증가하면 O(n) 탐색
- eBPF는 해시 맵 기반 → O(1) 조회
- iptables는 conntrack 모듈 사용 → 메모리 및 CPU 오버헤드
- eBPF는 커널 내에서 직접 패킷을 수정하여 context switch 최소화

##### HTTP 헬스체크가 검증하는 것

| 체크 대상 | URL | 검증 내용 |
|-----------|-----|-----------|
| **프론트엔드** | `http://NodeIP:30173` | nginx가 살아있고, ConfigMap에서 마운트된 정적 파일(index.html)을 정상 서빙하는지 확인. HTTP 200이면 OK |
| **API** | `http://NodeIP:30461/api/health` | uvicorn 프로세스가 실행 중이고, FastAPI 앱이 로드 완료되었으며, DB 연결이 가능한지 확인 |
| **Keycloak** | `http://NodeIP:30080` | Keycloak JBoss/Quarkus 서버가 부팅 완료되어 로그인 페이지를 렌더링할 수 있는지 확인 |

헬스체크가 실패하는 경우의 원인 체인:

```
curl 실패 원인 추적:

  curl: connection refused
    └─ NodePort에 리스닝하는 프로세스 없음
       └─ kube-proxy/Cilium이 Service→Pod DNAT 규칙을 아직 등록 안 함
          └─ Endpoint 객체가 없음 (Pod가 Ready가 아님)
             └─ Pod readinessProbe 실패
                └─ 컨테이너 내부 프로세스가 아직 시작 안 됨
                   └─ pip install 진행 중 (백엔드) 또는 Keycloak 부팅 중
```

### 최적화 효과

| 최적화 항목 | Before | After |
|-------------|--------|-------|
| DB/Keycloak 배포 | 순차 실행 | 병렬 apply |
| 프론트 빌드 | 매번 `npm install + build` | 변경 없으면 스킵 |
| pip install | `--no-cache-dir` (매번 다운로드) | hostPath 캐시 재사용 |
| Health Check | 순차 대기 (프론트→API→KC) | 3개 동시 백그라운드 |
| Cilium 복구 | 무조건 Pod 재시작 | Running이면 스킵 |

전체 소요 시간: **약 1~3분** (캐시 활용 시 대폭 단축)

---

## 3단계: 접속 확인

스크립트가 완료되면 아래 URL로 접속합니다:

| 서비스 | URL | 설명 |
|--------|-----|------|
| 웹 UI | `http://192.168.64.5:30173` | MES 프론트엔드 (14개 메뉴) |
| API 문서 | `http://192.168.64.5:30461/docs` | Swagger UI (37개 엔드포인트) |
| Keycloak | `http://192.168.64.5:30080` | 인증 관리 콘솔 |

> API 서버는 Pod 시작 시 `pip install`을 수행합니다. 최초 기동 시 1~2분 소요되나, 이후 pip 캐시가 유지되어 재기동이 빨라집니다.

---

## 상태 확인 명령어

```bash
# Pod 전체 상태 확인
kubectl get pods -o wide

# API 서버 로그 확인 (pip install 진행 여부)
kubectl logs deployment/mes-api --tail=30

# 프론트엔드 로그 확인
kubectl logs deployment/mes-frontend --tail=20

# 노드 상태 확인
kubectl get nodes

# 서비스 포트 확인
kubectl get svc
```

---

## 문제 해결 (Troubleshooting)

### 1. K8s API 서버 연결 실패 (60초 타임아웃)

```bash
# kubelet 상태 확인
systemctl status kubelet

# swap이 활성화되어 있으면 kubelet이 죽음
swapoff -a
systemctl restart kubelet

# 30초 후 확인
kubectl get nodes
```

**원인**: VM 재부팅 시 swap이 다시 활성화되어 kubelet이 기동 실패

### 2. Pod가 ContainerCreating에서 멈춤

```bash
# Cilium 네트워크 문제 — CNI Pod 재시작
kubectl delete pod -n kube-system -l k8s-app=cilium --force
sleep 10
kubectl get pods -n kube-system
```

**원인**: Cilium eBPF 네트워크 플러그인이 VM 재시작 후 초기화 실패

### 3. API 서버 502/Connection Refused

```bash
# Pod 로그 확인 — pip install 진행 중일 수 있음
kubectl logs deployment/mes-api --tail=30

# 완전히 실패한 경우 강제 재배포
kubectl rollout restart deployment mes-api
```

**원인**: pip install이 아직 진행 중이거나, DB 연결 실패

### 4. 프론트엔드 빈 화면 (흰 화면)

```bash
# ConfigMap 재생성
cd /root/MES_PROJECT/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend
```

**원인**: 빌드 파일이 ConfigMap에 반영되지 않음

### 5. DB 데이터가 초기화됨

```bash
# 현재 DB 확인
kubectl exec deployment/postgres -- psql -U postgres -d mes_db -c "SELECT count(*) FROM items;"

# 데이터가 없으면 init.sql 재실행
kubectl exec -i deployment/postgres -- psql -U postgres -d mes_db < /root/MES_PROJECT/db/init.sql
```

**원인**: PV(PersistentVolume) hostPath 디렉터리가 초기화됨

---

## 수동 개별 배포 (참고)

init.sh를 사용하지 않고 개별 컴포넌트를 수동으로 배포하는 방법입니다.

### DB만 배포

```bash
cd /root/MES_PROJECT
kubectl apply -f infra/postgres-pv.yaml
kubectl apply -f infra/db-secret.yaml
kubectl apply -f infra/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres --timeout=90s
```

### 백엔드만 재배포

```bash
cd /root/MES_PROJECT
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/
kubectl apply -f infra/mes-api.yaml
kubectl rollout restart deployment mes-api
```

### 프론트엔드만 재배포

```bash
cd /root/MES_PROJECT/frontend
npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl apply -f ../infra/nginx-config.yaml
kubectl apply -f ../infra/mes-frontend.yaml
kubectl rollout restart deployment mes-frontend
```

### K8s 리소스 전체 한 번에 적용

```bash
kubectl apply -f /root/MES_PROJECT/infra/
```

---

## 시스템 종료

시스템을 안전하게 종료하려면:

```bash
# 애플리케이션 Pod 스케일 다운
kubectl scale deployment mes-api mes-frontend --replicas=0

# 또는 VM 자체를 종료
shutdown -h now
```

다음 부팅 시 `bash /root/MES_PROJECT/init.sh`를 다시 실행하면 됩니다.

---

## 요약 플로우

```
VM 부팅
  │
  ├─ SSH 접속: ssh c1_master1@192.168.64.5
  │
  ├─ root 전환: sudo -s
  │
  ├─ 시작 스크립트: bash /root/MES_PROJECT/init.sh
  │   ├─ [1~4] 시스템설정 → K8s API → 네트워크(스킵가능) → Pod정리
  │   ├─ [5+6] DB + Keycloak ─── 병렬 배포 ───┐
  │   ├─ [7]   백엔드 배포 (pip 캐시 활용)     │
  │   ├─ [8+9] 프론트 빌드(캐시) + 배포        │
  │   ├─ [10]  서비스 Health Check ── 병렬 대기 ┘
  │   └─ [11]  Keycloak 설정 (Realm/사용자)
  │
  │   ████████████████████ 100%  ● ● ● ● ● ● ● ● ● ● ●  [2:15 소요]
  │
  └─ 브라우저 접속: http://192.168.64.5:30173
```

---

**최종 업데이트**: 2026-03-12
