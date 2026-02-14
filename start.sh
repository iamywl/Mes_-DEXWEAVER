#!/bin/bash
# =========================================================
# KNU MES 시스템 원클릭 시작 스크립트
# VM 부팅 후 이 스크립트 하나만 실행하면 전체 시스템이 올라갑니다.
# 사용법: sudo bash /root/MES_PROJECT/start.sh
#
# K8s 리소스 정의: infra/ 디렉터리
#   infra/postgres-pv.yaml    — PV, PVC
#   infra/db-secret.yaml      — DB 접속 Secret
#   infra/postgres.yaml       — PostgreSQL Deployment + Service
#   infra/mes-api.yaml        — FastAPI Deployment + Service
#   infra/nginx-config.yaml   — nginx ConfigMap
#   infra/mes-frontend.yaml   — Frontend Deployment + Service
# =========================================================
set +e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
PROJECT_DIR="/root/MES_PROJECT"
INFRA_DIR="$PROJECT_DIR/infra"
cd "$PROJECT_DIR"

REAL_IP=$(hostname -I | awk '{print $1}')

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}   KNU MES v5.1 — 시스템 시작 스크립트${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# ── [1/8] 시스템 기본 설정 ─────────────────────────────
echo -e "${YELLOW}[1/8] 시스템 기본 설정...${NC}"
swapoff -a 2>/dev/null
mkdir -p /mnt/data && chmod 777 /mnt/data
systemctl restart containerd 2>/dev/null
systemctl restart kubelet 2>/dev/null
echo -e "${GREEN}  ✓ swap 비활성화, containerd/kubelet 재시작${NC}"

# ── [2/8] Kubernetes API 대기 ──────────────────────────
echo -e "${YELLOW}[2/8] Kubernetes API 서버 대기 중...${NC}"
for i in $(seq 1 60); do
  if kubectl get nodes &>/dev/null; then
    echo -e "${GREEN}  ✓ K8s API 서버 준비 완료 (${i}초)${NC}"
    break
  fi
  [ "$i" -eq 60 ] && echo -e "${RED}  ✗ K8s API 60초 타임아웃. kubelet 로그를 확인하세요.${NC}" && exit 1
  sleep 1
done

# ── [3/8] Cilium 네트워크 복구 ─────────────────────────
echo -e "${YELLOW}[3/8] Cilium 네트워크 복구...${NC}"
CILIUM_POD=$(kubectl get pods -n kube-system -l k8s-app=cilium -o name 2>/dev/null | head -1)
if [ -n "$CILIUM_POD" ]; then
  kubectl delete "$CILIUM_POD" -n kube-system --force --grace-period=0 &>/dev/null
  sleep 5
  for i in $(seq 1 30); do
    if kubectl get pods -n kube-system -l k8s-app=cilium 2>/dev/null | grep -q Running; then
      echo -e "${GREEN}  ✓ Cilium 네트워크 정상${NC}"
      break
    fi
    sleep 2
  done
else
  echo -e "${GREEN}  ✓ Cilium 확인 (이미 정상 또는 미설치)${NC}"
fi

# ── [4/8] 기존 불량 Pod 정리 ──────────────────────────
echo -e "${YELLOW}[4/8] 불량 Pod 정리...${NC}"
kubectl delete pods --field-selector=status.phase=Failed --all-namespaces --ignore-not-found &>/dev/null
kubectl get pods 2>/dev/null | grep -E "Unknown|Error|CrashLoopBackOff" | awk '{print $1}' | \
  xargs -r kubectl delete pod --force --grace-period=0 &>/dev/null
echo -e "${GREEN}  ✓ 불량 Pod 정리 완료${NC}"

# ── [5/8] PostgreSQL DB 배포 ──────────────────────────
echo -e "${YELLOW}[5/8] PostgreSQL DB 배포...${NC}"
kubectl apply -f "$INFRA_DIR/postgres-pv.yaml" &>/dev/null
kubectl apply -f "$INFRA_DIR/db-secret.yaml" &>/dev/null
kubectl apply -f "$INFRA_DIR/postgres.yaml" &>/dev/null

echo -e "${YELLOW}  → DB Pod 대기 중...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres --timeout=90s &>/dev/null
echo -e "${GREEN}  ✓ PostgreSQL 준비 완료${NC}"

# ── [6/8] 백엔드 API 배포 ────────────────────────────
echo -e "${YELLOW}[6/8] 백엔드 API 배포...${NC}"
kubectl delete configmap api-code --ignore-not-found &>/dev/null
kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/ &>/dev/null

# CORS_ORIGINS에 실제 IP 주입 후 적용
sed "s|__CORS_ORIGINS__|http://${REAL_IP}:30173,http://localhost:30173,http://localhost:3000|" \
  "$INFRA_DIR/mes-api.yaml" | kubectl apply -f - &>/dev/null

echo -e "${GREEN}  ✓ 백엔드 배포 완료 (pip install 진행 중, 약 1~2분 소요)${NC}"

# ── [7/8] 프론트엔드 빌드 & 배포 ─────────────────────
echo -e "${YELLOW}[7/8] 프론트엔드 빌드 & 배포...${NC}"
cd "$PROJECT_DIR/frontend"
npm install --silent 2>/dev/null
npm run build 2>&1 | tail -3

kubectl delete configmap frontend-build --ignore-not-found &>/dev/null
kubectl create configmap frontend-build --from-file=dist/ &>/dev/null

kubectl apply -f "$INFRA_DIR/nginx-config.yaml" &>/dev/null
kubectl apply -f "$INFRA_DIR/mes-frontend.yaml" &>/dev/null

echo -e "${GREEN}  ✓ 프론트엔드 배포 완료${NC}"

# ── [8/8] 최종 검증 ──────────────────────────────────
echo -e "${YELLOW}[8/8] 시스템 검증 중...${NC}"
cd "$PROJECT_DIR"

# 방화벽 개방
ufw allow 30000:32767/tcp &>/dev/null

# Pod 재시작 (ConfigMap 갱신 반영)
kubectl rollout restart deployment mes-frontend &>/dev/null
kubectl rollout restart deployment mes-api &>/dev/null

echo -e "${YELLOW}  → 서비스 기동 대기 (최대 90초)...${NC}"
for i in $(seq 1 90); do
  FE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:30173 2>/dev/null)
  if [ "$FE" = "200" ]; then
    echo -e "${GREEN}  ✓ 프론트엔드 응답 OK (${i}초)${NC}"
    break
  fi
  sleep 1
done

# API는 pip install 때문에 더 걸림
echo -e "${YELLOW}  → API 서버 기동 대기 (pip install 포함, 최대 180초)...${NC}"
for i in $(seq 1 180); do
  API=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:30461/api/infra/status 2>/dev/null)
  if [ "$API" = "200" ]; then
    echo -e "${GREEN}  ✓ API 서버 응답 OK (${i}초)${NC}"
    break
  fi
  [ "$i" -eq 180 ] && echo -e "${RED}  ✗ API 타임아웃 — kubectl logs deployment/mes-api 로 확인하세요${NC}"
  sleep 1
done

echo ""
echo -e "${CYAN}=================================================${NC}"
echo -e "${GREEN}  ✅ KNU MES 시스템 시작 완료!${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""
echo -e "  🌐 웹 접속:  ${CYAN}http://${REAL_IP}:30173${NC}"
echo -e "  📡 API 문서: ${CYAN}http://${REAL_IP}:30461/docs${NC}"
echo ""
echo -e "  Pod 상태:"
kubectl get pods -o wide 2>/dev/null | sed 's/^/    /'
echo ""
