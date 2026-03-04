"""REQ-042: MQTT 데이터 수집 — 브로커 설정 + 센서 실시간 조회 (FN-054~055)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


# ── FN-054: MQTT 브로커 설정 ────────────────────────────────

async def save_mqtt_config(data: dict) -> dict:
    """MQTT 브로커 설정 저장."""
    broker_url = data.get("broker_url", "").strip()
    if not broker_url:
        return {"error": "broker_url은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        topics = data.get("topics", [])
        config_ids = []

        for topic in topics:
            cursor.execute(
                """INSERT INTO mqtt_config
                   (broker_url, topic_pattern, equip_code, sensor_type,
                    collect_interval_sec, is_active)
                   VALUES (%s, %s, %s, %s, %s, TRUE)
                   RETURNING config_id""",
                (broker_url, topic.get("pattern", ""),
                 topic.get("equip_code"), topic.get("sensor_type"),
                 data.get("collect_interval_sec", 10)),
            )
            config_ids.append(cursor.fetchone()[0])

        if not topics:
            cursor.execute(
                """INSERT INTO mqtt_config (broker_url, collect_interval_sec, is_active)
                   VALUES (%s, %s, TRUE) RETURNING config_id""",
                (broker_url, data.get("collect_interval_sec", 10)),
            )
            config_ids.append(cursor.fetchone()[0])

        conn.commit()
        cursor.close()
        return {"success": True, "config_ids": config_ids,
                "broker_url": broker_url, "topics_count": len(topics)}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("MQTT 설정 저장 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_mqtt_configs() -> dict:
    """MQTT 설정 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT config_id, broker_url, topic_pattern, equip_code,
                      sensor_type, collect_interval_sec, is_active, created_at
               FROM mqtt_config ORDER BY created_at DESC""",
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "config_id": r[0], "broker_url": r[1], "topic_pattern": r[2],
                    "equip_code": r[3], "sensor_type": r[4],
                    "collect_interval_sec": r[5], "is_active": r[6],
                    "created_at": r[7].isoformat() if r[7] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


# ── FN-055: 센서 데이터 실시간 조회 ─────────────────────────

async def get_realtime_sensor(equip_code: str,
                               sensor_type: str = None,
                               minutes: int = 30,
                               interval: str = "raw") -> dict:
    """센서 데이터 실시간 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        if interval == "raw":
            sql = """SELECT sensor_type, value, collected_at
                     FROM sensor_data
                     WHERE equip_code = %s
                       AND collected_at >= NOW() - INTERVAL '%s minutes'"""
            params = [equip_code, minutes]
            if sensor_type and sensor_type != "all":
                sql += " AND sensor_type = %s"
                params.append(sensor_type)
            sql += " ORDER BY collected_at"
            cursor.execute(sql, tuple(params))
        else:
            # 집계 (1min / 5min)
            bucket = 1 if interval == "1min" else 5
            sql = """SELECT sensor_type,
                            AVG(value) AS avg_val,
                            date_trunc('hour', collected_at)
                              + (EXTRACT(MINUTE FROM collected_at)::int / %s * %s)
                              * INTERVAL '1 minute' AS bucket_time
                     FROM sensor_data
                     WHERE equip_code = %s
                       AND collected_at >= NOW() - INTERVAL '%s minutes'"""
            params = [bucket, bucket, equip_code, minutes]
            if sensor_type and sensor_type != "all":
                sql += " AND sensor_type = %s"
                params.append(sensor_type)
            sql += " GROUP BY sensor_type, bucket_time ORDER BY bucket_time"
            cursor.execute(sql, tuple(params))

        rows = cursor.fetchall()

        # 센서별 그룹핑
        sensors = {}
        for r in rows:
            st = r[0]
            if st not in sensors:
                sensors[st] = {"type": st, "data": [], "values": []}
            val = float(r[1]) if r[1] else 0
            sensors[st]["data"].append({
                "timestamp": r[2].isoformat() if r[2] else None,
                "value": round(val, 4),
            })
            sensors[st]["values"].append(val)

        # 통계 계산
        result_sensors = []
        for st, info in sensors.items():
            vals = info["values"]
            n = len(vals)
            avg_v = sum(vals) / n if n else 0
            std_v = (sum((v - avg_v) ** 2 for v in vals) / n) ** 0.5 if n > 1 else 0
            result_sensors.append({
                "type": st,
                "data": info["data"],
                "stats": {
                    "min": round(min(vals), 4) if vals else 0,
                    "max": round(max(vals), 4) if vals else 0,
                    "avg": round(avg_v, 4),
                    "std": round(std_v, 4),
                    "count": n,
                },
            })

        # 마지막 수신 시각
        cursor.execute(
            "SELECT MAX(collected_at) FROM sensor_data WHERE equip_code = %s",
            (equip_code,),
        )
        last_row = cursor.fetchone()
        last_received = last_row[0].isoformat() if last_row and last_row[0] else None

        cursor.close()
        return {
            "equip_code": equip_code,
            "sensors": result_sensors,
            "last_received": last_received,
        }
    except Exception as e:
        log.error("센서 데이터 조회 오류: %s", e)
        return {"error": "센서 데이터 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def insert_sensor_data(data: dict) -> dict:
    """센서 데이터 수동 입력 (테스트/수동 수집용)."""
    equip_code = data.get("equip_code", "").strip()
    sensor_type = data.get("sensor_type", "").strip()
    value = data.get("value")

    if not equip_code or not sensor_type or value is None:
        return {"error": "equip_code, sensor_type, value는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO sensor_data (equip_code, sensor_type, value, source)
               VALUES (%s, %s, %s, %s)""",
            (equip_code, sensor_type, value,
             data.get("source", "MANUAL")),
        )
        conn.commit()
        cursor.close()
        return {"success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
