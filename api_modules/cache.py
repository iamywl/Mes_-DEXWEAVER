"""NFR-006/009: Redis 캐시 유틸리티 — 선택적 Redis, fallback 메모리 캐시."""

import json
import logging
import os
import time

log = logging.getLogger(__name__)

_redis = None
_memory_cache: dict[str, tuple[float, str]] = {}  # key → (expire_ts, json_value)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_TTL = 300  # 5분


def _get_redis():
    """Redis 연결 (lazy init). 실패 시 None → 메모리 캐시 fallback."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis as redis_lib
        _redis = redis_lib.from_url(REDIS_URL, decode_responses=True,
                                     socket_connect_timeout=2)
        _redis.ping()
        log.info("Redis connected: %s", REDIS_URL)
        return _redis
    except Exception as e:
        log.warning("Redis unavailable, using memory cache: %s", e)
        _redis = False  # 재시도 방지
        return None


def cache_get(key: str) -> dict | None:
    """캐시 조회. 히트 시 dict, 미스 시 None."""
    r = _get_redis()
    if r:
        try:
            val = r.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass
    else:
        entry = _memory_cache.get(key)
        if entry and entry[0] > time.time():
            return json.loads(entry[1])
        elif entry:
            del _memory_cache[key]
    return None


def cache_set(key: str, value: dict, ttl: int = DEFAULT_TTL):
    """캐시 저장."""
    json_val = json.dumps(value, default=str)
    r = _get_redis()
    if r:
        try:
            r.setex(key, ttl, json_val)
        except Exception:
            pass
    else:
        _memory_cache[key] = (time.time() + ttl, json_val)


def cache_delete(pattern: str):
    """캐시 삭제 (패턴 지원)."""
    r = _get_redis()
    if r:
        try:
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
        except Exception:
            pass
    else:
        to_del = [k for k in _memory_cache if k.startswith(pattern.rstrip("*"))]
        for k in to_del:
            del _memory_cache[k]


def cache_flush():
    """전체 캐시 초기화."""
    r = _get_redis()
    if r:
        try:
            r.flushdb()
        except Exception:
            pass
    _memory_cache.clear()
