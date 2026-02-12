"""REQ-024: Defect prediction using historical data and threshold scoring."""

from api_modules.database import get_db, release_conn


async def predict_defect_probability(process_params: dict):
    """Predict defect probability based on process parameters.

    Queries defect_history table for dynamic threshold ranges derived
    from low-defect production runs. Falls back to static thresholds
    if DB is unavailable.

    Args:
        process_params: Dict with keys temperature, pressure,
            speed, humidity.

    Returns:
        Dict with defect_probability, main_causes, recommended_action.
    """
    conn = None
    try:
        conn = get_db()
        if not conn:
            return _static_predict(process_params)

        cursor = conn.cursor()

        query = """
            SELECT
                AVG(temperature)    AS avg_temp,
                STDDEV(temperature) AS std_temp,
                AVG(pressure)       AS avg_pres,
                STDDEV(pressure)    AS std_pres,
                AVG(speed)          AS avg_spd,
                STDDEV(speed)       AS std_spd,
                AVG(humidity)       AS avg_hum,
                STDDEV(humidity)    AS std_hum
            FROM defect_history
            WHERE total_count > 0
              AND (defect_count::numeric / total_count) < 0.05;
        """
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()

        if row and row[0] is not None:
            thresholds = {
                "temperature": {
                    "min": float(row[0]) - 2 * float(row[1] or 10),
                    "max": float(row[0]) + 2 * float(row[1] or 10),
                    "weight": 0.4,
                },
                "pressure": {
                    "min": float(row[2]) - 2 * float(row[3] or 1),
                    "max": float(row[2]) + 2 * float(row[3] or 1),
                    "weight": 0.3,
                },
                "speed": {
                    "min": float(row[4]) - 2 * float(row[5] or 3),
                    "max": float(row[4]) + 2 * float(row[5] or 3),
                    "weight": 0.2,
                },
                "humidity": {
                    "min": float(row[6]) - 2 * float(row[7] or 5),
                    "max": float(row[6]) + 2 * float(row[7] or 5),
                    "weight": 0.1,
                },
            }
        else:
            thresholds = _default_thresholds()

        return _score_params(process_params, thresholds)

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


def _default_thresholds():
    """Return static threshold config."""
    return {
        "temperature": {"min": 180, "max": 220, "weight": 0.4},
        "pressure": {"min": 8, "max": 12, "weight": 0.3},
        "speed": {"min": 45, "max": 55, "weight": 0.2},
        "humidity": {"min": 50, "max": 70, "weight": 0.1},
    }


def _static_predict(process_params):
    """Fallback prediction using static thresholds."""
    return _score_params(process_params, _default_thresholds())


def _score_params(process_params, thresholds):
    """Score process parameters against thresholds."""
    defect_prob = 0.0
    causes = []
    for param, cfg in thresholds.items():
        val = process_params.get(param)
        if val is not None and not (cfg["min"] <= val <= cfg["max"]):
            defect_prob += cfg["weight"]
            causes.append(
                f"{param} ({val}) out of range "
                f"({cfg['min']:.1f}-{cfg['max']:.1f})."
            )

    defect_prob = min(1.0, defect_prob)
    return {
        "defect_probability": round(defect_prob * 100, 2),
        "main_causes": causes if causes else ["No deviations."],
        "recommended_action": (
            "Monitor closely." if defect_prob > 0 else "Stable."
        ),
    }
