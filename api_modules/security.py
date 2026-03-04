"""NFR-007/012/013: 보안 강화 — Rate Limiting, 로그인 잠금, 보안 이벤트 로깅."""

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
            log.warning("Login blocked — account locked: %s", user_id)
            return f"계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요."
        else:
            # 잠금 해제
            del _locked_accounts[user_id]
            _login_failures.pop(user_id, None)
    return None


def record_login_failure(user_id: str):
    """로그인 실패 기록. 5회 초과 시 잠금."""
    now = time.time()
    cutoff = now - FAILURE_WINDOW_MINUTES * 60
    # 윈도우 내 실패만 유지
    _login_failures[user_id] = [t for t in _login_failures[user_id] if t > cutoff]
    _login_failures[user_id].append(now)

    count = len(_login_failures[user_id])
    log.warning("Login failure #%d for user: %s", count, user_id)

    if count >= MAX_FAILURES:
        _locked_accounts[user_id] = now + LOCKOUT_MINUTES * 60
        log.warning("Account locked for %d min: %s", LOCKOUT_MINUTES, user_id)


def record_login_success(user_id: str):
    """로그인 성공 시 실패 카운터 초기화."""
    _login_failures.pop(user_id, None)
    _locked_accounts.pop(user_id, None)


def log_security_event(event_type: str, detail: str, user_id: str = None,
                        ip: str = None):
    """보안 이벤트 로깅 (KISA 49 감사 로그)."""
    log.info("SECURITY_EVENT | type=%s | user=%s | ip=%s | %s",
             event_type, user_id or "-", ip or "-", detail)
