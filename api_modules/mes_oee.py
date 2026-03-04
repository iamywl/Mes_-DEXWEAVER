"""FN-044~045: OEE 자동계산 — 설비별 OEE, 대시보드."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def get_oee(equip_code: str, start_date: str = None, end_date: str = None) -> dict:
    """FN-044: OEE 자동 계산."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 설비 존재 확인
        cursor.execute("SELECT name FROM equipments WHERE equip_code = %s", (equip_code,))
        equip = cursor.fetchone()
        if not equip:
            cursor.close()
            return {"error": f"설비 {equip_code}를 찾을 수 없습니다."}

        # 캐시된 OEE 먼저 조회
        sql = """SELECT calc_date, planned_time, downtime, total_count, good_count,
                        availability, performance, quality_rate, oee
                 FROM oee_daily WHERE equip_code = %s"""
        params = [equip_code]
        if start_date:
            sql += " AND calc_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND calc_date <= %s"
            params.append(end_date)
        sql += " ORDER BY calc_date DESC"

        cursor.execute(sql, tuple(params))
        cached = cursor.fetchall()

        if cached:
            daily = [{
                "date": str(r[0]),
                "planned_time": float(r[1] or 480),
                "downtime": float(r[2] or 0),
                "total_count": r[3] or 0,
                "good_count": r[4] or 0,
                "availability": float(r[5] or 0),
                "performance": float(r[6] or 0),
                "quality_rate": float(r[7] or 0),
                "oee": float(r[8] or 0),
            } for r in cached]
            cursor.close()
            avg_oee = sum(d["oee"] for d in daily) / len(daily) if daily else 0
            return {
                "equip_code": equip_code,
                "equip_name": equip[0],
                "daily": daily,
                "average_oee": round(avg_oee, 4),
            }

        # 캐시 없으면 실시간 계산
        result = await _calculate_oee_realtime(cursor, equip_code, equip[0])
        cursor.close()
        return result
    except Exception as e:
        log.error("OEE calculation error: %s", e)
        return {"error": "OEE 계산 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def _calculate_oee_realtime(cursor, equip_code, equip_name):
    """실시간 OEE 계산 (캐시 없을 때)."""
    # 작업실적에서 데이터 집계
    cursor.execute(
        """SELECT wo.work_date,
                  SUM(wr.good_qty + wr.defect_qty) as total,
                  SUM(wr.good_qty) as good,
                  COUNT(DISTINCT wr.result_id) as result_count
           FROM work_results wr
           JOIN work_orders wo ON wr.wo_id = wo.wo_id
           WHERE wo.equip_code = %s
           GROUP BY wo.work_date
           ORDER BY wo.work_date DESC
           LIMIT 30""",
        (equip_code,))
    rows = cursor.fetchall()

    # 설비 다운타임 (equip_status_log에서)
    cursor.execute(
        """SELECT DATE(changed_at) as dt,
                  COUNT(*) FILTER (WHERE status = 'DOWN') as down_events
           FROM equip_status_log
           WHERE equip_code = %s
           GROUP BY DATE(changed_at)""",
        (equip_code,))
    downtime_map = {str(r[0]): r[1] * 30 for r in cursor.fetchall()}  # 이벤트당 30분 추정

    daily = []
    for work_date, total, good, _ in rows:
        dt = str(work_date)
        planned_time = 480  # 8시간 기본
        downtime = downtime_map.get(dt, 0)
        operating_time = max(planned_time - downtime, 1)

        # Availability
        avail = operating_time / planned_time

        # Performance (이론 CT 기반 — 설비 capacity_per_hour 사용)
        cursor.execute("SELECT capacity_per_hour FROM equipments WHERE equip_code = %s",
                        (equip_code,))
        cap = cursor.fetchone()
        capacity = cap[0] if cap else 100
        ideal_ct = 60 / capacity  # 분/개
        perf = (ideal_ct * total) / operating_time if operating_time > 0 else 0
        perf = min(perf, 1.0)

        # Quality
        qual = good / total if total > 0 else 1.0

        oee = avail * perf * qual

        daily.append({
            "date": dt,
            "planned_time": planned_time,
            "downtime": downtime,
            "total_count": total,
            "good_count": good,
            "availability": round(avail, 4),
            "performance": round(perf, 4),
            "quality_rate": round(qual, 4),
            "oee": round(oee, 4),
        })

    avg_oee = sum(d["oee"] for d in daily) / len(daily) if daily else 0
    return {
        "equip_code": equip_code,
        "equip_name": equip_name,
        "daily": daily,
        "average_oee": round(avg_oee, 4),
    }


async def get_oee_dashboard() -> dict:
    """FN-045: OEE 대시보드 — 전체 설비 OEE 요약."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 최근 OEE 집계 (설비별 최신 7일 평균)
        cursor.execute(
            """SELECT e.equip_code, e.name, e.status,
                      AVG(o.oee) as avg_oee,
                      AVG(o.availability) as avg_a,
                      AVG(o.performance) as avg_p,
                      AVG(o.quality_rate) as avg_q,
                      COUNT(o.oee_id) as days
               FROM equipments e
               LEFT JOIN oee_daily o ON e.equip_code = o.equip_code
                   AND o.calc_date >= CURRENT_DATE - INTERVAL '7 days'
               GROUP BY e.equip_code, e.name, e.status
               ORDER BY avg_oee DESC NULLS LAST""")
        rows = cursor.fetchall()

        equipments = []
        total_oee = 0
        counted = 0
        for r in rows:
            oee_val = float(r[3]) if r[3] else None
            equip = {
                "equip_code": r[0],
                "name": r[1],
                "status": r[2],
                "oee": round(oee_val, 4) if oee_val else None,
                "availability": round(float(r[4]), 4) if r[4] else None,
                "performance": round(float(r[5]), 4) if r[5] else None,
                "quality_rate": round(float(r[6]), 4) if r[6] else None,
                "data_days": r[7],
            }
            if oee_val:
                total_oee += oee_val
                counted += 1
            # OEE 등급
            if oee_val:
                equip["grade"] = ("WORLD_CLASS" if oee_val >= 0.85
                                  else "GOOD" if oee_val >= 0.65
                                  else "AVERAGE" if oee_val >= 0.40
                                  else "POOR")
            equipments.append(equip)

        plant_oee = total_oee / counted if counted else 0
        cursor.close()
        return {
            "plant_oee": round(plant_oee, 4),
            "equipments": equipments,
            "total_equipment": len(equipments),
        }
    except Exception as e:
        log.error("OEE dashboard error: %s", e)
        return {"error": "OEE 대시보드 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
