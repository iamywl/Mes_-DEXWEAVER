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

## init.sh 가 수행하는 작업 (9단계)

> 모든 설정값은 `env.sh`에서 읽습니다 (하드코딩 없음).

| 단계 | 작업 | 설명 | 예상 소요 |
|------|------|------|-----------|
| **1/9** | 시스템 설정 | swap 비활성화, containerd/kubelet 재시작 | 즉시 |
| **2/9** | K8s API 대기 | Kubernetes API 서버가 응답할 때까지 대기 | 5~30초 |
| **3/9** | 네트워크 복구 | Cilium CNI Pod 재시작으로 클러스터 네트워크 복구 | 10~30초 |
| **4/9** | Pod 정리 | Unknown/Error/CrashLoopBackOff 상태의 불량 Pod 삭제 | 즉시 |
| **5/9** | DB 배포 | PostgreSQL PV/PVC 생성, Deployment 배포, Secret 생성 | 10~30초 |
| **6/9** | Keycloak 배포 | Keycloak 인증 서버 Deployment 배포 | 30~60초 |
| **7/9** | 백엔드 배포 | Python 소스 ConfigMap 생성, FastAPI Deployment 배포 | 즉시 |
| **8/9** | 프론트엔드 | `npm run build` → ConfigMap 생성 → nginx Deployment 배포 | 10~20초 |
| **9/9** | 검증 | 방화벽 개방, Pod 재시작, HTTP 응답 확인, Keycloak Realm 설정 | 30~180초 |

전체 소요 시간: **약 2~5분** (API 서버 pip install 포함)

---

## 3단계: 접속 확인

스크립트가 완료되면 아래 URL로 접속합니다:

| 서비스 | URL | 설명 |
|--------|-----|------|
| 웹 UI | `http://192.168.64.5:30173` | MES 프론트엔드 (14개 메뉴) |
| API 문서 | `http://192.168.64.5:30461/docs` | Swagger UI (37개 엔드포인트) |
| Keycloak | `http://192.168.64.5:30080` | 인증 관리 콘솔 |

> API 서버는 Pod 시작 시 `pip install`을 수행하므로, 최초 기동 시 1~2분 후 응답합니다.

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
  │   ├─ [1/9] swap off, kubelet restart
  │   ├─ [2/9] K8s API 대기
  │   ├─ [3/9] Cilium 복구
  │   ├─ [4/9] 불량 Pod 정리
  │   ├─ [5/9] PostgreSQL 배포
  │   ├─ [6/9] Keycloak 인증 서버 배포
  │   ├─ [7/9] FastAPI 백엔드 배포
  │   ├─ [8/9] React 프론트엔드 빌드 & 배포
  │   └─ [9/9] 검증 + Keycloak Realm 설정
  │
  └─ 브라우저 접속: http://192.168.64.5:30173
```

---

**최종 업데이트**: 2026-02-14
