"""REQ-024, FN-028: Defect prediction using XGBoost+SHAP (fallback: threshold scoring)."""

import logging
import numpy as np
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

try:
    import xgboost as xgb
    import shap
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    log.warning("XGBoost/SHAP not installed – falling back to threshold scoring.")


async def predict_defect_probability(process_params: dict) -> dict:
    """Predict defect probability based on process parameters.

    Uses XGBoost model trained on defect_history data with SHAP
    for factor contribution analysis. Falls back to threshold
    scoring if libraries unavailable or insufficient training data.
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return _threshold_predict(process_params)

        cursor = conn.cursor()

        # Load training data from defect_history
        cursor.execute(
            "SELECT temperature, pressure, speed, humidity, "
            "defect_count, total_count "
            "FROM defect_history "
            "WHERE total_count > 0 "
            "ORDER BY recorded_at DESC LIMIT 500"
        )
        rows = cursor.fetchall()
        cursor.close()

        if HAS_XGBOOST and len(rows) >= 10:
            return _xgboost_predict(rows, process_params)
        else:
            return _threshold_predict(process_params, rows if rows else None)

    except Exception as e:
        log.error("Defect prediction error: %s", e)
        return _threshold_predict(process_params)
    finally:
        if conn:
            release_conn(conn)


def _xgboost_predict(rows, process_params):
    """XGBoost-based prediction with SHAP factor analysis."""
    feature_names = ["temperature", "pressure", "speed", "humidity"]

    # Build training data
    X_train = []
    y_train = []
    for row in rows:
        temp, pres, spd, hum, defects, total = row
        features = [
            float(temp) if temp else 0,
            float(pres) if pres else 0,
            float(spd) if spd else 0,
            float(hum) if hum else 0,
        ]
        X_train.append(features)
        defect_rate = float(defects) / float(total) if total > 0 else 0
        y_train.append(defect_rate)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    # Train XGBoost model
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Predict for input params
    X_input = np.array([[
        float(process_params.get("temperature", process_params.get("temp", 200))),
        float(process_params.get("pressure", 10)),
        float(process_params.get("speed", 50)),
        float(process_params.get("humidity", 55)),
    ]])

    predicted_rate = float(model.predict(X_input)[0])
    predicted_rate = max(0.0, min(1.0, predicted_rate))

    # SHAP analysis for factor contributions
    factors = []
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_input)
        for i, name in enumerate(feature_names):
            factors.append({
                "name": name,
                "value": float(X_input[0][i]),
                "contribution": round(float(shap_values[0][i]), 4),
            })
        factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    except Exception:
        # Fallback to feature importance if SHAP fails
        importances = model.feature_importances_
        for i, name in enumerate(feature_names):
            factors.append({
                "name": name,
                "value": float(X_input[0][i]),
                "contribution": round(float(importances[i]), 4),
            })

    # Risk level and recommendation
    if predicted_rate > 0.1:
        risk_level = "HIGH"
        recommendation = "즉시 공정 파라미터 조정 필요. " + (
            f"주요 원인: {factors[0]['name']}" if factors else ""
        )
    elif predicted_rate > 0.05:
        risk_level = "MEDIUM"
        recommendation = "공정 파라미터 모니터링 강화 권장"
    else:
        risk_level = "LOW"
        recommendation = "정상 범위 - 현재 설정 유지"

    return {
        "model": "XGBoost",
        "defect_prob": round(predicted_rate * 100, 1),
        "risk_level": risk_level,
        "factors": factors,
        "recommendation": recommendation,
        "training_samples": len(rows),
    }


def _threshold_predict(process_params, training_data=None):
    """Threshold-based fallback prediction."""
    if training_data and len(training_data) >= 5:
        # Derive dynamic thresholds from data
        temps = [float(r[0]) for r in training_data if r[0]]
        press = [float(r[1]) for r in training_data if r[1]]
        spds = [float(r[2]) for r in training_data if r[2]]
        hums = [float(r[3]) for r in training_data if r[3]]

        def _range(vals):
            if not vals:
                return 0, 999
            avg = sum(vals) / len(vals)
            std = (sum((v - avg) ** 2 for v in vals) / len(vals)) ** 0.5
            return avg - 2 * std, avg + 2 * std

        thresholds = {
            "temperature": {"min": _range(temps)[0], "max": _range(temps)[1], "weight": 0.4},
            "pressure": {"min": _range(press)[0], "max": _range(press)[1], "weight": 0.3},
            "speed": {"min": _range(spds)[0], "max": _range(spds)[1], "weight": 0.2},
            "humidity": {"min": _range(hums)[0], "max": _range(hums)[1], "weight": 0.1},
        }
    else:
        thresholds = {
            "temperature": {"min": 180, "max": 220, "weight": 0.4},
            "pressure": {"min": 8, "max": 12, "weight": 0.3},
            "speed": {"min": 45, "max": 55, "weight": 0.2},
            "humidity": {"min": 50, "max": 70, "weight": 0.1},
        }

    defect_prob = 0.0
    factors = []
    for param, cfg in thresholds.items():
        val = process_params.get(param, process_params.get(param[:4]))
        if val is not None:
            val = float(val)
            if not (cfg["min"] <= val <= cfg["max"]):
                score = cfg["weight"]
                defect_prob += score
                factors.append({
                    "name": param,
                    "value": val,
                    "contribution": round(score, 4),
                })

    defect_prob = min(1.0, defect_prob)

    if defect_prob > 0.3:
        risk_level = "HIGH"
        recommendation = "공정 파라미터 즉시 조정 필요"
    elif defect_prob > 0.1:
        risk_level = "MEDIUM"
        recommendation = "파라미터 모니터링 강화 권장"
    else:
        risk_level = "LOW"
        recommendation = "정상 범위"

    return {
        "model": "ThresholdScoring",
        "defect_prob": round(defect_prob * 100, 1),
        "risk_level": risk_level,
        "factors": factors,
        "recommendation": recommendation,
    }
