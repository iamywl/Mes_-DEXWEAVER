"""NFR-003: AI 모델 캐싱 — Prophet/XGBoost/IsolationForest 학습 모델 저장/재사용.

학습된 모델을 pickle(joblib)로 디스크에 저장하고, 메모리 캐시를 병행하여
캐시 히트 시 재학습 없이 바로 예측을 수행한다.
"""

import logging
import os
import time
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

MODEL_DIR = os.getenv("MES_MODEL_CACHE_DIR", "/tmp/mes_models")
CACHE_TTL_HOURS = int(os.getenv("AI_MODEL_CACHE_TTL_HOURS", "24"))

# in-memory 캐시 (프로세스 내)
_memory_cache: dict = {}

try:
    import joblib
    _HAS_JOBLIB = True
except ImportError:
    _HAS_JOBLIB = False
    log.warning("joblib not available — model caching disabled")


class ModelCache:
    """디스크 + 메모리 2-tier 모델 캐시."""

    @staticmethod
    def get_or_train(model_key: str, train_func, data, max_age_hours: int = None):
        """캐시된 모델 반환 또는 train_func 호출 후 캐싱.

        Args:
            model_key: 캐시 키 (파일명에 사용)
            train_func: callable(data) -> trained model
            data: train_func에 전달할 데이터
            max_age_hours: 캐시 유효 시간 (기본 CACHE_TTL_HOURS)
        Returns:
            학습된 모델 객체
        """
        if max_age_hours is None:
            max_age_hours = CACHE_TTL_HOURS

        # 1. 메모리 캐시 확인
        if model_key in _memory_cache:
            entry = _memory_cache[model_key]
            if time.time() - entry["ts"] < max_age_hours * 3600:
                log.debug("Model memory cache hit: %s", model_key)
                return entry["model"]
            else:
                del _memory_cache[model_key]

        if not _HAS_JOBLIB:
            model = train_func(data)
            _memory_cache[model_key] = {"model": model, "ts": time.time()}
            return model

        os.makedirs(MODEL_DIR, exist_ok=True)
        path = os.path.join(MODEL_DIR, f"{model_key}.joblib")

        # 2. 디스크 캐시 확인
        if os.path.exists(path):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if datetime.now() - mtime < timedelta(hours=max_age_hours):
                    model = joblib.load(path)
                    _memory_cache[model_key] = {"model": model, "ts": os.path.getmtime(path)}
                    log.info("Model disk cache hit: %s", model_key)
                    return model
            except Exception as e:
                log.warning("Cache load failed for %s: %s", model_key, e)

        # 3. 캐시 미스 — 학습 후 저장
        log.info("Model cache miss — training: %s", model_key)
        model = train_func(data)
        try:
            joblib.dump(model, path, compress=3)
            _memory_cache[model_key] = {"model": model, "ts": time.time()}
        except Exception as e:
            log.warning("Cache save failed for %s: %s", model_key, e)
        return model

    @staticmethod
    def invalidate(model_key: str):
        """캐시 무효화."""
        _memory_cache.pop(model_key, None)
        if not _HAS_JOBLIB:
            return
        path = os.path.join(MODEL_DIR, f"{model_key}.joblib")
        if os.path.exists(path):
            os.remove(path)
            log.info("Model cache invalidated: %s", model_key)

    @staticmethod
    def clear_all():
        """전체 캐시 삭제."""
        global _memory_cache
        _memory_cache = {}
        if os.path.exists(MODEL_DIR):
            for f in os.listdir(MODEL_DIR):
                if f.endswith(".joblib"):
                    os.remove(os.path.join(MODEL_DIR, f))
            log.info("All model caches cleared")

    @staticmethod
    def get_stats() -> dict:
        """캐시 통계."""
        disk_count = 0
        disk_size = 0
        if os.path.exists(MODEL_DIR):
            for f in os.listdir(MODEL_DIR):
                if f.endswith(".joblib"):
                    disk_count += 1
                    disk_size += os.path.getsize(os.path.join(MODEL_DIR, f))

        return {
            "memory_count": len(_memory_cache),
            "disk_count": disk_count,
            "disk_size_mb": round(disk_size / 1024 / 1024, 2),
            "model_dir": MODEL_DIR,
            "cache_ttl_hours": CACHE_TTL_HOURS,
        }
