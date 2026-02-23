#!/bin/bash
# =========================================================
# KNU MES 시스템 — 통합 초기화 스크립트 (최적화 버전)
# VM 부팅 후 이 스크립트 하나만 실행하면 전체 시스템이 올라갑니다.
# 모든 설정은 env.sh에서 읽습니다 (하드코딩 없음).
#
# 사용법: sudo bash /root/MES_PROJECT/init.sh
#
# 최적화 포인트:
#   - 병렬 배포: DB/Keycloak/Backend를 동시에 배포
#   - 프론트엔드 빌드 캐시: dist/ 존재 시 빌드 스킵
#   - 병렬 Health Check: 서비스 상태를 동시에 확인
#   - 실시간 프로그레스 바: 경과시간 + 단계별 상태
# =========================================================
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"

# ── 프로그레스 태스크 등록 ────────────────────────────────
boot_timer_start

progress_add "시스템설정"
progress_add "K8s API"
progress_add "네트워크"
progress_add "Pod정리"
progress_add "DB배포"
progress_add "Keycloak"
progress_add "백엔드"
progress_add "프론트빌드"
progress_add "프론트배포"
progress_add "서비스대기"
progress_add "KC설정"

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}   KNU MES v${MES_VERSION} — 시스템 초기화 (최적화)${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# ── [1] 시스템 기본 설정 ─────────────────────────────────
progress_set "시스템설정" "run"
swapoff -a 2>/dev/null
mkdir -p /mnt/data && chmod 777 /mnt/data
systemctl restart containerd 2>/dev/null
systemctl restart kubelet 2>/dev/null
progress_set "시스템설정" "done"

# ── [2] Kubernetes API 대기 ──────────────────────────────
progress_set "K8s API" "run"
for i in $(seq 1 "${TIMEOUT_K8S_API}"); do
  if kubectl get nodes &>/dev/null; then
    log_ok "K8s API 서버 준비 완료 (${i}초)"
    break
  fi
  if [ "$i" -eq "${TIMEOUT_K8S_API}" ]; then
    log_err "K8s API ${TIMEOUT_K8S_API}초 타임아웃"
    progress_set "K8s API" "fail"
    exit 1
  fi
  sleep 1
done
progress_set "K8s API" "done"

# ── [3] Cilium 네트워크 복구 ─────────────────────────────
progress_set "네트워크" "run"
CILIUM_POD=$(kubectl get pods -n kube-system -l k8s-app=cilium -o name 2>/dev/null | head -1)
if [ -n "$CILIUM_POD" ]; then
  # Cilium이 이미 Running이면 재시작 스킵
  if kubectl get pods -n kube-system -l k8s-app=cilium 2>/dev/null | grep -q Running; then
    log_ok "Cilium 이미 정상 (재시작 스킵)"
  else
    kubectl delete "$CILIUM_POD" -n kube-system --force --grace-period=0 &>/dev/null
    for i in $(seq 1 30); do
      if kubectl get pods -n kube-system -l k8s-app=cilium 2>/dev/null | grep -q Running; then
        log_ok "Cilium 네트워크 복구 완료 (${i}초)"
        break
      fi
      sleep 2
    done
  fi
else
  log_ok "Cilium 확인 (미설치 또는 정상)"
fi
progress_set "네트워크" "done"

# ── [4] 기존 불량 Pod 정리 ──────────────────────────────
progress_set "Pod정리" "run"
kubectl delete pods --field-selector=status.phase=Failed --all-namespaces --ignore-not-found &>/dev/null
kubectl get pods 2>/dev/null | grep -E "Unknown|Error|CrashLoopBackOff" | awk '{print $1}' | \
  xargs -r kubectl delete pod --force --grace-period=0 &>/dev/null
progress_set "Pod정리" "done"

# ── [5+6+7] DB / Keycloak / Backend 병렬 배포 ───────────
# DB, Keycloak, Backend를 동시에 apply (서로 독립적)
progress_set "DB배포" "run"
progress_set "Keycloak" "run"

# DB 배포
kubectl apply -f "${INFRA_DIR}/postgres-pv.yaml" &>/dev/null
kubectl apply -f "${INFRA_DIR}/db-secret.yaml" &>/dev/null
kubectl apply -f "${INFRA_DIR}/postgres.yaml" &>/dev/null

# Keycloak 배포 (DB와 독립적)
kubectl apply -f "${INFRA_DIR}/keycloak.yaml" &>/dev/null

# DB Ready 대기 (Backend가 DB에 의존하므로)
kubectl wait --for=condition=ready pod -l app=postgres --timeout="${TIMEOUT_DB}s" &>/dev/null
progress_set "DB배포" "done"

# Backend 배포 (DB Ready 이후)
progress_set "백엔드" "run"
kubectl delete configmap api-code --ignore-not-found &>/dev/null
kubectl create configmap api-code \
  --from-file=app.py="${PROJECT_DIR}/app.py" \
  --from-file="${PROJECT_DIR}/api_modules/" &>/dev/null

sed "s|__CORS_ORIGINS__|${CORS_ORIGINS}|" \
  "${INFRA_DIR}/mes-api.yaml" | kubectl apply -f - &>/dev/null
progress_set "백엔드" "done"

# Keycloak은 배포 요청만 완료 (기동은 백그라운드)
progress_set "Keycloak" "done"

# ── [8] 프론트엔드 빌드 (캐시 활용) ─────────────────────
progress_set "프론트빌드" "run"
cd "${FRONTEND_DIR}"

if [ -d "dist" ] && [ "$(ls -A dist/ 2>/dev/null)" ]; then
  # dist/가 이미 있으면 소스 변경 확인
  NEED_BUILD=false
  # src/ 파일 중 dist보다 새로운 파일이 있으면 재빌드
  if [ -n "$(find src/ -newer dist/index.html -name '*.jsx' -o -name '*.js' -o -name '*.css' 2>/dev/null | head -1)" ]; then
    NEED_BUILD=true
  fi

  if [ "$NEED_BUILD" = false ]; then
    log_ok "프론트엔드 빌드 캐시 사용 (스킵)"
  else
    log_info "소스 변경 감지 → 재빌드..."
    npm install --silent 2>/dev/null
    npm run build 2>&1 | tail -3
  fi
else
  log_info "최초 빌드 실행 중..."
  npm install --silent 2>/dev/null
  npm run build 2>&1 | tail -3
fi
progress_set "프론트빌드" "done"

# ── [9] 프론트엔드 배포 ─────────────────────────────────
progress_set "프론트배포" "run"
kubectl delete configmap frontend-build --ignore-not-found &>/dev/null
kubectl create configmap frontend-build --from-file=dist/ &>/dev/null
kubectl apply -f "${INFRA_DIR}/nginx-config.yaml" &>/dev/null
kubectl apply -f "${INFRA_DIR}/mes-frontend.yaml" &>/dev/null

# ConfigMap 갱신 반영
kubectl rollout restart deployment mes-frontend &>/dev/null
kubectl rollout restart deployment mes-api &>/dev/null
progress_set "프론트배포" "done"

# ── [10] 서비스 Health Check (병렬) ─────────────────────
progress_set "서비스대기" "run"

# 방화벽 개방
ufw allow 30000:32767/tcp &>/dev/null

# 세 서비스를 백그라운드에서 동시에 대기
WAIT_DIR=$(mktemp -d)

(
  wait_for_http_code "http://localhost:${PORT_FRONTEND}" "200" "${TIMEOUT_FRONTEND}" "프론트엔드"
  echo $? > "${WAIT_DIR}/frontend"
) &
PID_FE=$!

(
  wait_for_http_code "http://localhost:${PORT_API}/api/infra/status" "200" "${TIMEOUT_API}" "API 서버"
  echo $? > "${WAIT_DIR}/api"
) &
PID_API=$!

(
  wait_for_url "http://localhost:${PORT_KEYCLOAK}/realms/master" "${TIMEOUT_KEYCLOAK}" "Keycloak"
  echo $? > "${WAIT_DIR}/keycloak"
) &
PID_KC=$!

# 대기 중 프로그레스 표시
while kill -0 $PID_FE 2>/dev/null || kill -0 $PID_API 2>/dev/null || kill -0 $PID_KC 2>/dev/null; do
  progress_render
  sleep 2
done
wait $PID_FE $PID_API $PID_KC 2>/dev/null

progress_set "서비스대기" "done"

# ── [11] Keycloak 설정 ──────────────────────────────────
progress_set "KC설정" "run"
KC_RESULT=$(cat "${WAIT_DIR}/keycloak" 2>/dev/null)
if [ "$KC_RESULT" = "0" ]; then
  bash "${PROJECT_DIR}/setup-keycloak.sh" 2>/dev/null
  progress_set "KC설정" "done"
else
  log_warn "Keycloak 미응답 — 설정 스킵"
  progress_set "KC설정" "fail"
fi

rm -rf "${WAIT_DIR}"

# ── 완료 ─────────────────────────────────────────────────
echo ""
echo -e "${CYAN}=================================================${NC}"
echo -e "${GREEN}  KNU MES v${MES_VERSION} 시스템 시작 완료! [$(boot_elapsed) 소요]${NC}"
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
