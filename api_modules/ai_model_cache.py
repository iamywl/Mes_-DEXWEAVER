"""AI 모델 캐싱 매니저 — 학습된 모델을 디스크에 캐싱하여 재사용."""

import logging
import os
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

MODEL_DIR = os.getenv("MES_MODEL_CACHE_DIR", "/tmp/mes_models")

try:
    import joblib
    _HAS_JOBLIB = True
except ImportError:
    _HAS_JOBLIB = False
    log.warning("joblib not available — model caching disabled")


class ModelCache:
    """디스크 기반 모델 캐시."""

    @staticmethod
    def get_or_train(model_key: str, train_func, data, max_age_hours: int = 24):
        """캐시된 모델 반환 또는 train_func 호출 후 캐싱.

        Args:
            model_key: 캐시 키 (파일명에 사용)
            train_func: callable(data) -> trained model
            data: train_func에 전달할 데이터
            max_age_hours: 캐시 유효 시간 (기본 24시간)
        Returns:
            학습된 모델 객체
        """
        if not _HAS_JOBLIB:
            return train_func(data)

        os.makedirs(MODEL_DIR, exist_ok=True)
        path = os.path.join(MODEL_DIR, f"{model_key}.joblib")

        # 캐시 히트 확인
        if os.path.exists(path):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if datetime.now() - mtime < timedelta(hours=max_age_hours):
                    model = joblib.load(path)
                    log.info("Model cache hit: %s", model_key)
                    return model
            except Exception as e:
                log.warning("Cache load failed for %s: %s", model_key, e)

        # 캐시 미스 — 학습 후 저장
        log.info("Model cache miss — training: %s", model_key)
        model = train_func(data)
        try:
            joblib.dump(model, path)
        except Exception as e:
            log.warning("Cache save failed for %s: %s", model_key, e)
        return model

    @staticmethod
    def invalidate(model_key: str):
        """캐시 무효화."""
        if not _HAS_JOBLIB:
            return
        path = os.path.join(MODEL_DIR, f"{model_key}.joblib")
        if os.path.exists(path):
            os.remove(path)
            log.info("Model cache invalidated: %s", model_key)

    @staticmethod
    def clear_all():
        """전체 캐시 삭제."""
        if os.path.exists(MODEL_DIR):
            for f in os.listdir(MODEL_DIR):
                if f.endswith(".joblib"):
                    os.remove(os.path.join(MODEL_DIR, f))
            log.info("All model caches cleared")
