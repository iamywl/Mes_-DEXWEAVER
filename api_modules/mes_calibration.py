"""REQ-064: 교정 관리 — 주기 관리, 성적서, 만료 차단."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_gauge(data: dict) -> dict:
    """계측기 등록."""
    gauge_code = data.get("gauge_code", "").strip()
    if not gauge_code:
        return {"error": "gauge_code는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO calibrations
               (gauge_code, gauge_name, gauge_type, location,
                calibration_cycle_days, next_due)
               VALUES (%s,%s,%s,%s,%s, CURRENT_DATE + %s * INTERVAL '1 day')
               RETURNING calibration_id""",
            (gauge_code, data.get("gauge_name"), data.get("gauge_type"),
             data.get("location"), data.get("cycle_days", 365),
             data.get("cycle_days", 365)),
        )
        cal_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "calibration_id": cal_id, "gauge_code": gauge_code}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_gauges(status: str = None) -> dict:
    """계측기 목록 (상태 자동 업데이트)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 상태 자동 갱신
        cursor.execute("""
            UPDATE calibrations SET status = 'EXPIRED', is_blocked = TRUE
            WHERE next_due < CURRENT_DATE AND status != 'EXPIRED'""")
        cursor.execute("""
            UPDATE calibrations SET status = 'DUE_SOON'
            WHERE next_due BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
              AND status = 'VALID'""")
        conn.commit()

        sql = """SELECT calibration_id, gauge_code, gauge_name, gauge_type,
                        location, calibration_cycle_days, last_calibrated,
                        next_due, status, is_blocked, created_at
                 FROM calibrations WHERE 1=1"""
        params = []
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY next_due ASC LIMIT 500"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        return {
            "items": [
                {"calibration_id": r[0], "gauge_code": r[1], "gauge_name": r[2],
                 "gauge_type": r[3], "location": r[4], "cycle_days": r[5],
                 "last_calibrated": r[6].isoformat() if r[6] else None,
                 "next_due": r[7].isoformat() if r[7] else None,
                 "status": r[8], "is_blocked": r[9],
                 "created_at": r[10].isoformat() if r[10] else None}
                for r in rows
            ],
            "summary": {
                "valid": sum(1 for r in rows if r[8] == 'VALID'),
                "due_soon": sum(1 for r in rows if r[8] == 'DUE_SOON'),
                "expired": sum(1 for r in rows if r[8] == 'EXPIRED'),
            },
        }
    except Exception as e:
        log.error("교정 목록 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def record_calibration(calibration_id: int, data: dict) -> dict:
    """교정 실행 기록."""
    result = data.get("result", "").strip()
    if result not in ("PASS", "FAIL", "ADJUSTED"):
        return {"error": "result는 PASS/FAIL/ADJUSTED 중 하나여야 합니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 교정 주기 조회
        cursor.execute(
            "SELECT calibration_cycle_days FROM calibrations WHERE calibration_id = %s",
            (calibration_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": "계측기를 찾을 수 없습니다."}
        cycle = row[0]

        next_due_date = f"CURRENT_DATE + {cycle} * INTERVAL '1 day'"
        cursor.execute(
            f"""INSERT INTO calibration_records
               (calibration_id, performed_date, performed_by, result,
                certificate_no, deviation, notes, next_due)
               VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s,
                       CURRENT_DATE + %s * INTERVAL '1 day')
               RETURNING record_id""",
            (calibration_id, data.get("performed_by"),
             result, data.get("certificate_no"),
             data.get("deviation"), data.get("notes"), cycle),
        )
        record_id = cursor.fetchone()[0]

        # 계측기 상태 업데이트
        new_status = "VALID" if result in ("PASS", "ADJUSTED") else "EXPIRED"
        blocked = result == "FAIL"
        cursor.execute(
            """UPDATE calibrations SET last_calibrated = CURRENT_DATE,
                      next_due = CURRENT_DATE + %s * INTERVAL '1 day',
                      status = %s, is_blocked = %s
               WHERE calibration_id = %s""",
            (cycle, new_status, blocked, calibration_id),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "record_id": record_id, "status": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
