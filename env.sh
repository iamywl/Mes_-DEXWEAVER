#!/bin/bash
# =========================================================
# KNU MES 시스템 — 환경 설정 파일
# 모든 스크립트가 이 파일을 source하여 설정값을 읽습니다.
# 하드코딩 금지: 변경이 필요하면 이 파일만 수정하세요.
# =========================================================

# ── 프로젝트 경로 ──────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${PROJECT_DIR}/infra"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
DB_DIR="${PROJECT_DIR}/db"

# ── 네트워크 ───────────────────────────────────────────────
REAL_IP="${MES_IP:-$(hostname -I | awk '{print $1}')}"

# ── 서비스 포트 (NodePort) ─────────────────────────────────
PORT_FRONTEND="${MES_PORT_FRONTEND:-30173}"
PORT_API="${MES_PORT_API:-30461}"
PORT_KEYCLOAK="${MES_PORT_KEYCLOAK:-30080}"

# ── Keycloak 설정 ─────────────────────────────────────────
KC_URL="http://${REAL_IP}:${PORT_KEYCLOAK}"
KC_REALM="${MES_KC_REALM:-mes-realm}"
KC_CLIENT_ID="${MES_KC_CLIENT:-mes-frontend}"
KC_ADMIN_USER="${MES_KC_ADMIN_USER:-admin}"
KC_ADMIN_PASS="${MES_KC_ADMIN_PASS:-admin1234}"

# ── CORS 허용 오리진 ──────────────────────────────────────
CORS_ORIGINS="http://${REAL_IP}:${PORT_FRONTEND},http://localhost:${PORT_FRONTEND},http://localhost:3000"

# ── 타임아웃 (초) ─────────────────────────────────────────
TIMEOUT_K8S_API="${MES_TIMEOUT_K8S:-60}"
TIMEOUT_DB="${MES_TIMEOUT_DB:-90}"
TIMEOUT_API="${MES_TIMEOUT_API:-180}"
TIMEOUT_FRONTEND="${MES_TIMEOUT_FE:-90}"
TIMEOUT_KEYCLOAK="${MES_TIMEOUT_KC:-120}"

# ── 버전 ──────────────────────────────────────────────────
MES_VERSION="5.2"

# ── 색상 코드 (출력용) ─────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── 공통 유틸 함수 ─────────────────────────────────────────
log_info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}  ✓${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${YELLOW}[$1]${NC} $2"; }

wait_for_url() {
  local url="$1" timeout="$2" label="$3"
  for i in $(seq 1 "$timeout"); do
    if curl -s -o /dev/null -w '' --max-time 2 "$url" 2>/dev/null; then
      log_ok "${label} 응답 OK (${i}초)"
      return 0
    fi
    sleep 1
  done
  log_err "${label} ${timeout}초 타임아웃"
  return 1
}

wait_for_http_code() {
  local url="$1" expected="$2" timeout="$3" label="$4"
  for i in $(seq 1 "$timeout"); do
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$url" 2>/dev/null)
    if [ "$code" = "$expected" ]; then
      log_ok "${label} 응답 OK (${i}초)"
      return 0
    fi
    sleep 1
  done
  log_err "${label} ${timeout}초 타임아웃"
  return 1
}

# ── 프로그레스 바 유틸 ──────────────────────────────────────
BOOT_START_TIME=""
PROGRESS_TASKS=()          # ("label|status")  status: pending/run/done/fail
PROGRESS_FILE="/tmp/mes_boot_progress"

boot_timer_start() { BOOT_START_TIME=$(date +%s); }

boot_elapsed() {
  local now=$(date +%s)
  local diff=$((now - BOOT_START_TIME))
  printf "%d:%02d" $((diff / 60)) $((diff % 60))
}

# 태스크 등록: progress_add "라벨"
progress_add() {
  PROGRESS_TASKS+=("$1|pending")
}

# 태스크 상태 변경: progress_set "라벨" "run|done|fail"
progress_set() {
  local label="$1" new_status="$2"
  for i in "${!PROGRESS_TASKS[@]}"; do
    case "${PROGRESS_TASKS[$i]}" in
      "${label}|"*) PROGRESS_TASKS[$i]="${label}|${new_status}" ;;
    esac
  done
  progress_render
}

# 프로그레스 바 렌더링
progress_render() {
  local total=${#PROGRESS_TASKS[@]}
  local done=0 fail=0 running=""
  for entry in "${PROGRESS_TASKS[@]}"; do
    local lbl="${entry%%|*}" st="${entry##*|}"
    case "$st" in
      done) done=$((done + 1)) ;;
      fail) fail=$((fail + 1)); done=$((done + 1)) ;;
      run)  running="$lbl" ;;
    esac
  done

  local pct=0
  [ "$total" -gt 0 ] && pct=$((done * 100 / total))
  local filled=$((pct / 5))
  local empty=$((20 - filled))
  local bar=$(printf '█%.0s' $(seq 1 $filled 2>/dev/null))$(printf '░%.0s' $(seq 1 $empty 2>/dev/null))

  # 상태 아이콘 나열
  local icons=""
  for entry in "${PROGRESS_TASKS[@]}"; do
    local st="${entry##*|}"
    case "$st" in
      done) icons+="${GREEN}●${NC} " ;;
      fail) icons+="${RED}●${NC} " ;;
      run)  icons+="${YELLOW}◉${NC} " ;;
      *)    icons+="○ " ;;
    esac
  done

  echo -ne "\r\033[K"
  echo -ne "  ${CYAN}[$(boot_elapsed)]${NC} ${bar} ${pct}%  ${icons}"
  [ -n "$running" ] && echo -ne " ${YELLOW}${running}${NC}"
  [ "$done" -eq "$total" ] && echo ""
}
