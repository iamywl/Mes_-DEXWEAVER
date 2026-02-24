"""FN-013~014, FN-032~034: Equipment management module."""

import logging
from datetime import datetime, timedelta

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    HAS_IFOREST = True
except ImportError:
    np = None
    HAS_IFOREST = False
    log.warning("numpy/scikit-learn not installed – falling back to rule-based failure prediction.")


async def create_equipment(data: dict) -> dict:
    """FN-013: Register a new equipment."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Auto-generate equip_code
        cursor.execute(
            "SELECT equip_code FROM equipments "
            "ORDER BY equip_code DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            seq = int(row[0].split("-")[1]) + 1
        else:
            seq = 1
        equip_code = f"EQP-{seq:03d}"

        cursor.execute(
            "INSERT INTO equipments (equip_code, name, process_code, "
            "capacity_per_hour, status, install_date) "
            "VALUES (%s, %s, %s, %s, 'STOP', %s)",
            (
                equip_code,
                data["name"],
                data.get("process_code"),
                data.get("capacity_per_hour", 100),
                data.get("install_date"),
            ),
        )
        conn.commit()
        cursor.close()
        return {"equip_code": equip_code, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_equipments(process_code: str = None,
                         status: str = None) -> dict:
    """FN-014: List equipments with optional filters."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"equipments": []}

        cursor = conn.cursor()

        where = []
        params = []
        if process_code:
            where.append("e.process_code = %s")
            params.append(process_code)
        if status:
            where.append("e.status = %s")
            params.append(status)

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        cursor.execute(
            f"SELECT e.equip_code, e.name, e.process_code, "
            f"e.capacity_per_hour, e.status, e.install_date "
            f"FROM equipments e {where_sql} "
            f"ORDER BY e.equip_code",
            params,
        )
        rows = cursor.fetchall()
        cursor.close()

        equipments = [
            {
                "equip_code": r[0], "name": r[1],
                "process_code": r[2], "capacity_per_hour": r[3],
                "status": r[4], "install_date": str(r[5]) if r[5] else None,
            }
            for r in rows
        ]
        return {"equipments": equipments}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def update_status(equip_code: str, data: dict) -> dict:
    """FN-032: Change equipment status with downtime auto-calculation."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        new_status = data["status"]
        now = datetime.now()

        # Calculate downtime if transitioning from DOWN/STOP to RUNNING
        downtime_minutes = None
        cursor.execute(
            "SELECT status, changed_at FROM equip_status_log "
            "WHERE equip_code = %s ORDER BY changed_at DESC LIMIT 1",
            (equip_code,),
        )
        prev = cursor.fetchone()
        if prev and prev[0] in ("DOWN", "STOP") and new_status == "RUNNING":
            prev_time = prev[1]
            if prev_time:
                delta = now - prev_time
                downtime_minutes = round(delta.total_seconds() / 60, 1)

        cursor.execute(
            "UPDATE equipments SET status = %s WHERE equip_code = %s",
            (new_status, equip_code),
        )
        cursor.execute(
            "INSERT INTO equip_status_log (equip_code, status, reason, "
            "worker_id, changed_at) VALUES (%s, %s, %s, %s, %s)",
            (equip_code, new_status,
             data.get("reason"), data.get("worker_id"), now),
        )
        conn.commit()
        cursor.close()

        result = {"success": True, "changed_at": now.isoformat()}
        if downtime_minutes is not None:
            result["downtime_minutes"] = downtime_minutes
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_equipment_status() -> dict:
    """FN-033: Real-time equipment status dashboard with daily uptime rate."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"equipments": []}

        cursor = conn.cursor()

        # Get equipment list with current job
        cursor.execute(
            "SELECT e.equip_code, e.name, e.status, "
            "wo.wo_id AS current_job "
            "FROM equipments e "
            "LEFT JOIN work_orders wo ON e.equip_code = wo.equip_code "
            "AND wo.status = 'WORKING' "
            "ORDER BY e.equip_code"
        )
        rows = cursor.fetchall()

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get today's status log for all equipment
        cursor.execute(
            "SELECT equip_code, status, changed_at "
            "FROM equip_status_log "
            "WHERE changed_at >= %s "
            "ORDER BY equip_code, changed_at",
            (today_start,),
        )
        today_logs = cursor.fetchall()

        # Get last status before today for each equipment
        cursor.execute(
            "SELECT DISTINCT ON (equip_code) equip_code, status, changed_at "
            "FROM equip_status_log "
            "WHERE changed_at < %s "
            "ORDER BY equip_code, changed_at DESC",
            (today_start,),
        )
        pre_today = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.close()

        # Build per-equipment status timeline for today
        equip_logs = {}
        for log in today_logs:
            equip_logs.setdefault(log[0], []).append(
                (log[1], log[2])
            )

        elapsed = (now - today_start).total_seconds()

        equipments = []
        for r in rows:
            ec = r[0]
            logs = equip_logs.get(ec, [])

            # Calculate running seconds today
            running_secs = 0.0
            if logs:
                # Start with status before today
                prev_status = pre_today.get(ec, "STOP")
                prev_time = today_start
                for status, changed_at in logs:
                    if prev_status == "RUNNING":
                        running_secs += (changed_at - prev_time).total_seconds()
                    prev_status = status
                    prev_time = changed_at
                # From last log to now
                if prev_status == "RUNNING":
                    running_secs += (now - prev_time).total_seconds()
            else:
                # No logs today - use status before today
                prev_status = pre_today.get(ec, "STOP")
                if prev_status == "RUNNING":
                    running_secs = elapsed

            uptime_today = round(running_secs / elapsed, 2) if elapsed > 0 else 0.0

            equipments.append({
                "equip_code": ec, "name": r[1],
                "status": r[2], "current_job": r[3],
                "uptime_today": uptime_today,
            })

        return {"equipments": equipments}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def predict_failure(data: dict) -> dict:
    """FN-034: AI equipment failure prediction using IsolationForest + sensor data."""
    conn = None
    try:
        conn = get_conn()
        equip_code = data.get("equip_code")
        sensor = data.get("sensor", {})

        vibration = float(sensor.get("vibration", 0))
        temperature = float(sensor.get("temperature", 0))
        current_amp = float(sensor.get("current", 0))

        # Save sensor data first
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO equip_sensors (equip_code, vibration, "
                "temperature, current_amp) VALUES (%s, %s, %s, %s)",
                (equip_code, vibration, temperature, current_amp),
            )
            conn.commit()

            # Load historical sensor data for this equipment
            cursor.execute(
                "SELECT vibration, temperature, current_amp "
                "FROM equip_sensors WHERE equip_code = %s "
                "ORDER BY recorded_at DESC LIMIT 200",
                (equip_code,),
            )
            history = cursor.fetchall()
            cursor.close()
        else:
            history = []

        if HAS_IFOREST and len(history) >= 10:
            input_features = np.array([[vibration, temperature, current_amp]])
            result = _iforest_predict(history, input_features, equip_code)
        else:
            result = _rule_based_predict(vibration, temperature, current_amp)

        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


def _iforest_predict(history, input_features, equip_code):
    """IsolationForest anomaly detection with remaining life estimation."""
    X_hist = np.array([
        [float(r[0] or 0), float(r[1] or 0), float(r[2] or 0)]
        for r in history
    ])

    # Train IsolationForest
    clf = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
    )
    clf.fit(X_hist)

    # Anomaly score: sklearn returns negative scores (lower = more anomalous)
    raw_score = clf.decision_function(input_features)[0]
    # Convert to 0~1 scale (0=normal, 1=highly anomalous)
    anomaly_score = max(0.0, min(1.0, 0.5 - raw_score))

    # Factor contribution analysis using feature deviation from mean
    feature_names = ["vibration", "temperature", "current"]
    means = X_hist.mean(axis=0)
    stds = X_hist.std(axis=0)
    stds = np.where(stds == 0, 1, stds)  # prevent division by zero

    z_scores = np.abs((input_features[0] - means) / stds)
    total_z = z_scores.sum() if z_scores.sum() > 0 else 1

    factors = []
    for i, name in enumerate(feature_names):
        contribution = float(z_scores[i] / total_z) * anomaly_score
        factors.append({
            "name": name,
            "value": float(input_features[0][i]),
            "z_score": round(float(z_scores[i]), 2),
            "contribution": round(contribution, 4),
        })
    factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    # Remaining life estimation based on anomaly trend
    remaining_life = max(0, int((1 - anomaly_score) * 500))

    if anomaly_score > 0.7:
        recommendation = "즉시 점검 필요 - IsolationForest 이상 감지"
    elif anomaly_score > 0.4:
        recommendation = "48시간 내 점검 권장 - 이상 징후 감지"
    else:
        recommendation = "정상 범위"

    return {
        "model": "IsolationForest",
        "failure_prob": round(anomaly_score * 100, 1),
        "remaining_life_hours": remaining_life,
        "anomaly_score": round(anomaly_score, 4),
        "factors": factors,
        "recommendation": recommendation,
        "training_samples": len(history),
    }


def _rule_based_predict(vibration, temperature, current_amp):
    """Rule-based fallback prediction."""
    anomaly = 0.0
    factors = []

    if vibration > 3.0:
        score = min(1.0, (vibration - 3.0) / 3.0)
        anomaly += score * 0.4
        factors.append({
            "name": "vibration", "value": vibration,
            "contribution": round(score * 0.4, 4),
        })
    if temperature > 60:
        score = min(1.0, (temperature - 60) / 30.0)
        anomaly += score * 0.35
        factors.append({
            "name": "temperature", "value": temperature,
            "contribution": round(score * 0.35, 4),
        })
    if current_amp > 15:
        score = min(1.0, (current_amp - 15) / 10.0)
        anomaly += score * 0.25
        factors.append({
            "name": "current", "value": current_amp,
            "contribution": round(score * 0.25, 4),
        })

    anomaly = min(1.0, anomaly)
    remaining_life = max(0, int((1 - anomaly) * 500))

    if anomaly > 0.7:
        recommendation = "즉시 점검 필요"
    elif anomaly > 0.4:
        recommendation = "48시간 내 점검 권장"
    else:
        recommendation = "정상 범위"

    return {
        "model": "RuleBased",
        "failure_prob": round(anomaly * 100, 1),
        "remaining_life_hours": remaining_life,
        "anomaly_score": round(anomaly, 4),
        "factors": factors,
        "recommendation": recommendation,
    }
