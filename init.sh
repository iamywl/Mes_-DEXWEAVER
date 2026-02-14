#!/bin/bash
# =========================================================
# KNU MES 시스템 — 통합 초기화 스크립트
# VM 부팅 후 이 스크립트 하나만 실행하면 전체 시스템이 올라갑니다.
# 모든 설정은 env.sh에서 읽습니다 (하드코딩 없음).
#
# 사용법: sudo bash /root/MES_PROJECT/init.sh
#
# 하위 스크립트:
#   env.sh             — 환경 변수 및 공통 유틸
#   setup-keycloak.sh  — Keycloak Realm/Client/사용자 자동 설정
#
# K8s 리소스 정의: infra/ 디렉터리
#   infra/postgres-pv.yaml    — PV, PVC
#   infra/db-secret.yaml      — DB 접속 Secret
#   infra/postgres.yaml       — PostgreSQL Deployment + Service
#   infra/keycloak.yaml       — Keycloak 인증 서버
#   infra/mes-api.yaml        — FastAPI Deployment + Service
#   infra/nginx-config.yaml   — nginx ConfigMap
#   infra/mes-frontend.yaml   — Frontend Deployment + Service
# =========================================================
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"

TOTAL_STEPS=9
step=0
next_step() { step=$((step + 1)); log_step "${step}/${TOTAL_STEPS}" "$1"; }

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}   KNU MES v${MES_VERSION} — 시스템 초기화 스크립트${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# ── [1] 시스템 기본 설정 ─────────────────────────────────
next_step "시스템 기본 설정..."
swapoff -a 2>/dev/null
mkdir -p /mnt/data && chmod 777 /mnt/data
systemctl restart containerd 2>/dev/null
systemctl restart kubelet 2>/dev/null
log_ok "swap 비활성화, containerd/kubelet 재시작"

# ── [2] Kubernetes API 대기 ──────────────────────────────
next_step "Kubernetes API 서버 대기 중..."
for i in $(seq 1 "${TIMEOUT_K8S_API}"); do
  if kubectl get nodes &>/dev/null; then
    log_ok "K8s API 서버 준비 완료 (${i}초)"
    break
  fi
  if [ "$i" -eq "${TIMEOUT_K8S_API}" ]; then
    log_err "K8s API ${TIMEOUT_K8S_API}초 타임아웃. kubelet 로그를 확인하세요."
    exit 1
  fi
  sleep 1
done

# ── [3] Cilium 네트워크 복구 ─────────────────────────────
next_step "Cilium 네트워크 복구..."
CILIUM_POD=$(kubectl get pods -n kube-system -l k8s-app=cilium -o name 2>/dev/null | head -1)
if [ -n "$CILIUM_POD" ]; then
  kubectl delete "$CILIUM_POD" -n kube-system --force --grace-period=0 &>/dev/null
  sleep 5
  for i in $(seq 1 30); do
    if kubectl get pods -n kube-system -l k8s-app=cilium 2>/dev/null | grep -q Running; then
      log_ok "Cilium 네트워크 정상"
      break
    fi
    sleep 2
  done
else
  log_ok "Cilium 확인 (이미 정상 또는 미설치)"
fi

# ── [4] 기존 불량 Pod 정리 ──────────────────────────────
next_step "불량 Pod 정리..."
kubectl delete pods --field-selector=status.phase=Failed --all-namespaces --ignore-not-found &>/dev/null
kubectl get pods 2>/dev/null | grep -E "Unknown|Error|CrashLoopBackOff" | awk '{print $1}' | \
  xargs -r kubectl delete pod --force --grace-period=0 &>/dev/null
log_ok "불량 Pod 정리 완료"

# ── [5] PostgreSQL DB 배포 ──────────────────────────────
next_step "PostgreSQL DB 배포..."
kubectl apply -f "${INFRA_DIR}/postgres-pv.yaml" &>/dev/null
kubectl apply -f "${INFRA_DIR}/db-secret.yaml" &>/dev/null
kubectl apply -f "${INFRA_DIR}/postgres.yaml" &>/dev/null

log_info "DB Pod 대기 중..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout="${TIMEOUT_DB}s" &>/dev/null
log_ok "PostgreSQL 준비 완료"

# ── [6] Keycloak 인증 서버 배포 ────────────────────────
next_step "Keycloak 인증 서버 배포..."
kubectl apply -f "${INFRA_DIR}/keycloak.yaml" &>/dev/null
log_ok "Keycloak 배포 요청 완료 (기동 중, 약 30~60초 소요)"

# ── [7] 백엔드 API 배포 ────────────────────────────────
next_step "백엔드 API 배포..."
kubectl delete configmap api-code --ignore-not-found &>/dev/null
kubectl create configmap api-code \
  --from-file=app.py="${PROJECT_DIR}/app.py" \
  --from-file="${PROJECT_DIR}/api_modules/" &>/dev/null

# CORS_ORIGINS 플레이스홀더를 env.sh 값으로 치환 후 적용
sed "s|__CORS_ORIGINS__|${CORS_ORIGINS}|" \
  "${INFRA_DIR}/mes-api.yaml" | kubectl apply -f - &>/dev/null

log_ok "백엔드 배포 완료 (pip install 진행 중, 약 1~2분 소요)"

# ── [8] 프론트엔드 빌드 & 배포 ─────────────────────────
next_step "프론트엔드 빌드 & 배포..."
cd "${FRONTEND_DIR}"
npm install --silent 2>/dev/null
npm run build 2>&1 | tail -3

kubectl delete configmap frontend-build --ignore-not-found &>/dev/null
kubectl create configmap frontend-build --from-file=dist/ &>/dev/null

kubectl apply -f "${INFRA_DIR}/nginx-config.yaml" &>/dev/null
kubectl apply -f "${INFRA_DIR}/mes-frontend.yaml" &>/dev/null

log_ok "프론트엔드 배포 완료"

# ── [9] 최종 검증 + Keycloak 설정 ─────────────────────
next_step "시스템 검증 중..."
cd "${PROJECT_DIR}"

# 방화벽 개방
ufw allow 30000:32767/tcp &>/dev/null

# Pod 재시작 (ConfigMap 갱신 반영)
kubectl rollout restart deployment mes-frontend &>/dev/null
kubectl rollout restart deployment mes-api &>/dev/null

# 프론트엔드 대기
log_info "프론트엔드 기동 대기 (최대 ${TIMEOUT_FRONTEND}초)..."
wait_for_http_code "http://localhost:${PORT_FRONTEND}" "200" "${TIMEOUT_FRONTEND}" "프론트엔드"

# API 대기 (pip install 포함)
log_info "API 서버 기동 대기 (pip install 포함, 최대 ${TIMEOUT_API}초)..."
wait_for_http_code "http://localhost:${PORT_API}/api/infra/status" "200" "${TIMEOUT_API}" "API 서버"

# Keycloak 설정 (Realm, Client, 사용자 자동 생성)
log_info "Keycloak 기동 대기 (최대 ${TIMEOUT_KEYCLOAK}초)..."
if wait_for_url "http://localhost:${PORT_KEYCLOAK}/realms/master" "${TIMEOUT_KEYCLOAK}" "Keycloak"; then
  bash "${PROJECT_DIR}/setup-keycloak.sh" 2>/dev/null
fi

echo ""
echo -e "${CYAN}=================================================${NC}"
echo -e "${GREEN}  KNU MES v${MES_VERSION} 시스템 시작 완료!${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""
echo -e "  웹 접속:     ${CYAN}http://${REAL_IP}:${PORT_FRONTEND}${NC}"
echo -e "  API 문서:    ${CYAN}http://${REAL_IP}:${PORT_API}/docs${NC}"
echo -e "  Keycloak:    ${CYAN}http://${REAL_IP}:${PORT_KEYCLOAK}${NC}"
echo ""
echo -e "  테스트 계정: admin/${KC_ADMIN_PASS}, worker01/worker1234, viewer01/viewer1234"
echo ""
echo -e "  Pod 상태:"
kubectl get pods -o wide 2>/dev/null | sed 's/^/    /'
echo ""
