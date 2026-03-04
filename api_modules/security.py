"""NFR-007/012/013: 보안 강화 — Rate Limiting, 로그인 잠금, 보안 이벤트 로깅.

보안 이벤트 유형:
- LOGIN_SUCCESS / LOGIN_FAIL / LOGIN_BLOCKED
- AUTH_FAIL (토큰 인증 실패)
- PERMISSION_DENIED (권한 부족)
- ACCOUNT_LOCKED / ACCOUNT_UNLOCKED
"""

import logging
import time
from collections import defaultdict

log = logging.getLogger(__name__)

# ── 로그인 실패 추적 (메모리 기반, 프로세스 재시작 시 초기화) ───
_login_failures: dict[str, list[float]] = defaultdict(list)
_locked_accounts: dict[str, float] = {}  # user_id → unlock_time

MAX_FAILURES = 5
LOCKOUT_MINUTES = 15
FAILURE_WINDOW_MINUTES = 30


def check_login_lock(user_id: str) -> str | None:
    """로그인 잠금 상태 확인. 잠금 시 에러 메시지 반환, 아니면 None."""
    if user_id in _locked_accounts:
        unlock_at = _locked_accounts[user_id]
        if time.time() < unlock_at:
            remaining = int((unlock_at - time.time()) / 60) + 1
            return f"계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요."
        else:
            del _locked_accounts[user_id]
            _login_failures.pop(user_id, None)
            log_security_event("ACCOUNT_UNLOCKED", "잠금 기간 만료", user_id=user_id)
    return None


def record_login_failure(user_id: str):
    """로그인 실패 기록. 5회 초과 시 잠금."""
    now = time.time()
    cutoff = now - FAILURE_WINDOW_MINUTES * 60
    _login_failures[user_id] = [t for t in _login_failures[user_id] if t > cutoff]
    _login_failures[user_id].append(now)

    count = len(_login_failures[user_id])
    log.warning("Login failure #%d for user: %s", count, user_id)

    if count >= MAX_FAILURES:
        _locked_accounts[user_id] = now + LOCKOUT_MINUTES * 60
        log_security_event("ACCOUNT_LOCKED",
                           f"{LOCKOUT_MINUTES}분 잠금 (실패 {count}회)",
                           user_id=user_id)


def record_login_success(user_id: str):
    """로그인 성공 시 실패 카운터 초기화."""
    _login_failures.pop(user_id, None)
    _locked_accounts.pop(user_id, None)


def log_security_event(event_type: str, detail: str, user_id: str = None,
                        ip: str = None, severity: str = "INFO"):
    """보안 이벤트 로깅 (KISA 49 감사 로그).

    콘솔 로그 + DB 기록 (audit_log 테이블 사용 가능 시).
    """
    log.info("SECURITY_EVENT | type=%s | user=%s | ip=%s | severity=%s | %s",
             event_type, user_id or "-", ip or "-", severity, detail)

    # DB 기록 시도 (실패해도 무시 — 가용성 우선)
    _persist_security_event(event_type, detail, user_id, ip, severity)


def _persist_security_event(event_type: str, detail: str, user_id: str = None,
                             ip: str = None, severity: str = "INFO"):
    """보안 이벤트를 DB에 기록 (audit_log 테이블)."""
    try:
        from api_modules.database import get_conn, release_conn
        conn = get_conn()
        if not conn:
            return
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO audit_log (user_id, action, target_type, detail, ip_address)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id or 'system', f"SECURITY:{event_type}",
             'SECURITY', f"[{severity}] {detail}", ip),
        )
        conn.commit()
        cursor.close()
        release_conn(conn)
    except Exception:
        pass  # DB 미연결 시 무시 — 콘솔 로그는 이미 기록됨


def get_security_stats() -> dict:
    """현재 보안 상태 통계."""
    active_failures = {
        uid: len(times) for uid, times in _login_failures.items() if times
    }
    return {
        "locked_accounts": list(_locked_accounts.keys()),
        "locked_count": len(_locked_accounts),
        "active_failure_tracking": len(active_failures),
        "failure_details": active_failures,
        "config": {
            "max_failures": MAX_FAILURES,
            "lockout_minutes": LOCKOUT_MINUTES,
            "failure_window_minutes": FAILURE_WINDOW_MINUTES,
        },
    }
