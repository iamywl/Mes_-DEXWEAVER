"""FN-013~014, FN-032~034: Equipment management module."""

from api_modules.database import get_conn, release_conn


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
    """FN-032: Change equipment status."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        new_status = data["status"]

        cursor.execute(
            "UPDATE equipments SET status = %s WHERE equip_code = %s",
            (new_status, equip_code),
        )
        cursor.execute(
            "INSERT INTO equip_status_log (equip_code, status, reason, "
            "worker_id) VALUES (%s, %s, %s, %s)",
            (equip_code, new_status,
             data.get("reason"), data.get("worker_id")),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "changed_at": "now"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_equipment_status() -> dict:
    """FN-033: Real-time equipment status dashboard."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"equipments": []}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT e.equip_code, e.name, e.status, "
            "wo.wo_id AS current_job "
            "FROM equipments e "
            "LEFT JOIN work_orders wo ON e.equip_code = wo.equip_code "
            "AND wo.status = 'WORKING' "
            "ORDER BY e.equip_code"
        )
        rows = cursor.fetchall()
        cursor.close()

        equipments = [
            {
                "equip_code": r[0], "name": r[1],
                "status": r[2], "current_job": r[3],
            }
            for r in rows
        ]
        return {"equipments": equipments}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def predict_failure(data: dict) -> dict:
    """FN-034: AI equipment failure prediction using sensor data."""
    conn = None
    try:
        conn = get_conn()
        equip_code = data.get("equip_code")
        sensor = data.get("sensor", {})

        vibration = sensor.get("vibration", 0)
        temperature = sensor.get("temperature", 0)
        current_amp = sensor.get("current", 0)

        # Rule-based anomaly scoring
        anomaly = 0.0
        factors = []

        if vibration > 3.0:
            score = min(1.0, (vibration - 3.0) / 3.0)
            anomaly += score * 0.4
            factors.append({
                "name": "vibration", "contribution": round(score * 0.4, 2),
            })
        if temperature > 60:
            score = min(1.0, (temperature - 60) / 30.0)
            anomaly += score * 0.35
            factors.append({
                "name": "temperature", "contribution": round(score * 0.35, 2),
            })
        if current_amp > 15:
            score = min(1.0, (current_amp - 15) / 10.0)
            anomaly += score * 0.25
            factors.append({
                "name": "current", "contribution": round(score * 0.25, 2),
            })

        anomaly = min(1.0, anomaly)
        remaining_life = max(0, int((1 - anomaly) * 500))

        if anomaly > 0.7:
            recommendation = "즉시 점검 필요"
        elif anomaly > 0.4:
            recommendation = "48시간 내 점검 권장"
        else:
            recommendation = "정상 범위"

        # Save sensor data
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO equip_sensors (equip_code, vibration, "
                "temperature, current_amp) VALUES (%s, %s, %s, %s)",
                (equip_code, vibration, temperature, current_amp),
            )
            conn.commit()
            cursor.close()

        return {
            "failure_prob": round(anomaly * 100, 1),
            "remaining_life_hours": remaining_life,
            "anomaly_score": round(anomaly, 2),
            "factors": factors,
            "recommendation": recommendation,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
