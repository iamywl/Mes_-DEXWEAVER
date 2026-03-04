"""REQ-063: 에너지 관리 — 소비 모니터링, kWh/unit, 비용 분석."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def record_energy(data: dict) -> dict:
    """에너지 소비 데이터 입력."""
    equip_code = data.get("equip_code", "").strip()
    value = data.get("value")
    if not equip_code or value is None:
        return {"error": "equip_code, value는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO energy_consumption
               (equip_code, energy_type, value, unit, cost_per_unit, source)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (equip_code, data.get("energy_type", "ELECTRICITY"),
             value, data.get("unit", "kWh"),
             data.get("cost_per_unit"), data.get("source", "SENSOR")),
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


async def get_energy_dashboard(equip_code: str = None,
                                energy_type: str = None,
                                hours: int = 24) -> dict:
    """에너지 소비 대시보드."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        where = "WHERE recorded_at >= NOW() - INTERVAL '%s hours'"
        params = [hours]
        if equip_code:
            where += " AND equip_code = %s"
            params.append(equip_code)
        if energy_type:
            where += " AND energy_type = %s"
            params.append(energy_type)

        # 설비별 합계
        cursor.execute(
            f"""SELECT equip_code, energy_type,
                       SUM(value) AS total, AVG(value) AS avg_val,
                       MAX(value) AS peak,
                       SUM(value * COALESCE(cost_per_unit, 0)) AS total_cost
                FROM energy_consumption {where}
                GROUP BY equip_code, energy_type
                ORDER BY total DESC""",
            tuple(params),
        )
        rows = cursor.fetchall()

        # 시간별 추이
        cursor.execute(
            f"""SELECT date_trunc('hour', recorded_at) AS hr,
                       SUM(value) AS total
                FROM energy_consumption {where}
                GROUP BY hr ORDER BY hr""",
            tuple(params),
        )
        trend = [{"hour": r[0].isoformat() if r[0] else None,
                   "total": round(float(r[1]), 2)} for r in cursor.fetchall()]

        cursor.close()

        grand_total = sum(float(r[2]) for r in rows) if rows else 0
        grand_cost = sum(float(r[5]) for r in rows if r[5]) if rows else 0

        return {
            "period_hours": hours,
            "grand_total_kwh": round(grand_total, 2),
            "grand_total_cost": round(grand_cost, 2),
            "by_equipment": [
                {"equip_code": r[0], "energy_type": r[1],
                 "total": round(float(r[2]), 2), "avg": round(float(r[3]), 4),
                 "peak": round(float(r[4]), 2),
                 "cost": round(float(r[5]), 2) if r[5] else 0}
                for r in rows
            ],
            "hourly_trend": trend,
        }
    except Exception as e:
        log.error("에너지 대시보드 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_energy_per_unit() -> dict:
    """제품당 에너지 소비량(kWh/unit) — 작업실적 연계."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT e.equip_code,
                      SUM(e.value) AS total_kwh,
                      COALESCE(SUM(wr.good_qty), 1) AS total_units,
                      SUM(e.value) / GREATEST(SUM(wr.good_qty), 1) AS kwh_per_unit
               FROM energy_consumption e
               LEFT JOIN work_results wr ON wr.equip_code = e.equip_code
                 AND DATE(wr.created_at) = DATE(e.recorded_at)
               WHERE e.recorded_at >= NOW() - INTERVAL '7 days'
               GROUP BY e.equip_code
               ORDER BY kwh_per_unit DESC""",
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"equip_code": r[0], "total_kwh": round(float(r[1]), 2),
                 "total_units": int(r[2]), "kwh_per_unit": round(float(r[3]), 4)}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
