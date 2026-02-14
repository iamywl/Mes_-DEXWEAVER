#!/bin/bash
# =========================================================
# Keycloak 자동 설정 스크립트
# Realm, Client, 테스트 사용자를 REST API로 생성합니다.
# 모든 설정은 env.sh에서 읽습니다 (하드코딩 없음).
# =========================================================
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"

FRONTEND_URL="http://${REAL_IP}:${PORT_FRONTEND}"

log_info "Keycloak 설정 시작: ${KC_URL}"

# ── Admin 토큰 획득 ──────────────────────────────────────
log_info "Admin 토큰 획득..."
TOKEN=$(curl -s -X POST "${KC_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KC_ADMIN_USER}" \
  -d "password=${KC_ADMIN_PASS}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  log_err "Admin 토큰 획득 실패. Keycloak이 준비되지 않았습니다."
  exit 1
fi
log_ok "Admin 토큰 획득 완료"

AUTH="Authorization: Bearer ${TOKEN}"

# ── Realm 생성 ───────────────────────────────────────────
log_info "Realm '${KC_REALM}' 생성..."
curl -s -o /dev/null -w '' -X POST "${KC_URL}/admin/realms" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d "{
    \"realm\": \"${KC_REALM}\",
    \"enabled\": true,
    \"registrationAllowed\": false,
    \"loginWithEmailAllowed\": false,
    \"duplicateEmailsAllowed\": true
  }" 2>/dev/null
log_ok "Realm 생성 완료"

# ── Client 생성 ──────────────────────────────────────────
log_info "Client '${KC_CLIENT_ID}' 생성..."
curl -s -o /dev/null -w '' -X POST "${KC_URL}/admin/realms/${KC_REALM}/clients" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"${KC_CLIENT_ID}\",
    \"name\": \"MES Frontend\",
    \"publicClient\": true,
    \"directAccessGrantsEnabled\": true,
    \"standardFlowEnabled\": true,
    \"redirectUris\": [\"${FRONTEND_URL}/*\", \"http://localhost:3000/*\", \"http://localhost:${PORT_FRONTEND}/*\"],
    \"webOrigins\": [\"${FRONTEND_URL}\", \"http://localhost:3000\", \"http://localhost:${PORT_FRONTEND}\"],
    \"attributes\": {
      \"pkce.code.challenge.method\": \"S256\"
    }
  }" 2>/dev/null
log_ok "Client 생성 완료"

# ── 테스트 사용자 생성 함수 ──────────────────────────────
create_user() {
  local userid=$1 pass=$2 role=$3 name=$4
  curl -s -o /dev/null -w '' -X POST "${KC_URL}/admin/realms/${KC_REALM}/users" \
    -H "${AUTH}" -H "Content-Type: application/json" \
    -d "{
      \"username\": \"${userid}\",
      \"firstName\": \"${name}\",
      \"enabled\": true,
      \"credentials\": [{
        \"type\": \"password\",
        \"value\": \"${pass}\",
        \"temporary\": false
      }],
      \"attributes\": {
        \"role\": [\"${role}\"]
      }
    }" 2>/dev/null
  log_ok "${userid} (${role})"
}

# ── Realm Role 생성 ─────────────────────────────────────
log_info "Realm Role 생성..."
for role in admin worker viewer; do
  curl -s -o /dev/null -X POST "${KC_URL}/admin/realms/${KC_REALM}/roles" \
    -H "${AUTH}" -H "Content-Type: application/json" \
    -d "{\"name\": \"${role}\"}" 2>/dev/null
done
log_ok "Role 생성 완료 (admin, worker, viewer)"

# ── 사용자 생성 ─────────────────────────────────────────
log_info "테스트 사용자 생성..."
create_user "admin"    "${KC_ADMIN_PASS}" "admin"  "시스템관리자"
create_user "worker01" "worker1234"  "worker" "박작업자"
create_user "viewer01" "viewer1234"  "viewer" "조회전용A"

# ── 사용자에 Role 할당 ──────────────────────────────────
log_info "사용자 Role 할당..."
assign_role() {
  local userid=$1 rolename=$2
  local uid
  uid=$(curl -s "${KC_URL}/admin/realms/${KC_REALM}/users?username=${userid}" \
    -H "${AUTH}" | python3 -c "import sys,json; u=json.load(sys.stdin); print(u[0]['id'] if u else '')" 2>/dev/null)
  if [ -z "$uid" ]; then return; fi
  local rid
  rid=$(curl -s "${KC_URL}/admin/realms/${KC_REALM}/roles/${rolename}" \
    -H "${AUTH}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
  if [ -z "$rid" ]; then return; fi
  curl -s -o /dev/null -X POST "${KC_URL}/admin/realms/${KC_REALM}/users/${uid}/role-mappings/realm" \
    -H "${AUTH}" -H "Content-Type: application/json" \
    -d "[{\"id\":\"${rid}\",\"name\":\"${rolename}\"}]" 2>/dev/null
}
assign_role "admin"    "admin"
assign_role "worker01" "worker"
assign_role "viewer01" "viewer"
log_ok "Role 할당 완료"

echo ""
log_ok "Keycloak 설정 완료!"
echo -e "  Realm: ${KC_REALM}"
echo -e "  Client: ${KC_CLIENT_ID}"
echo -e "  관리 콘솔: ${KC_URL}"
echo -e "  테스트 계정: admin/${KC_ADMIN_PASS}, worker01/worker1234, viewer01/viewer1234"
