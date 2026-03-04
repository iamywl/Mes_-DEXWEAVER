"""REQ-061: FMEA 관리 — PFMEA CRUD, S/O/D, RPN 자동계산."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_fmea(data: dict) -> dict:
    """FMEA 문서 생성."""
    title = data.get("title", "").strip()
    if not title:
        return {"error": "title은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM fmea WHERE fmea_code LIKE %s",
                       (f"FMEA-{today}-%",))
        seq = (cursor.fetchone()[0] or 0) + 1
        fmea_code = f"FMEA-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO fmea (fmea_code, fmea_type, item_code, process_code,
                                  title, team_members, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING fmea_id""",
            (fmea_code, data.get("fmea_type", "PFMEA"),
             data.get("item_code"), data.get("process_code"),
             title, data.get("team_members"), data.get("created_by")),
        )
        fmea_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "fmea_id": fmea_id, "fmea_code": fmea_code}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("FMEA 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def add_fmea_item(fmea_id: int, data: dict) -> dict:
    """FMEA 항목(고장모드) 추가."""
    failure_mode = data.get("failure_mode", "").strip()
    if not failure_mode:
        return {"error": "failure_mode는 필수입니다."}

    s = data.get("severity", 1)
    o = data.get("occurrence", 1)
    d = data.get("detection", 1)

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO fmea_items
               (fmea_id, process_step, failure_mode, failure_effect, failure_cause,
                severity, occurrence, detection, recommended_action, action_owner, action_due)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING fmea_item_id""",
            (fmea_id, data.get("process_step"), failure_mode,
             data.get("failure_effect"), data.get("failure_cause"),
             s, o, d, data.get("recommended_action"),
             data.get("action_owner"), data.get("action_due")),
        )
        item_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "fmea_item_id": item_id, "rpn": s * o * d}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_fmea_list(item_code: str = None, status: str = None) -> dict:
    """FMEA 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = """SELECT fmea_id, fmea_code, fmea_type, item_code, process_code,
                        title, status, created_by, created_at FROM fmea WHERE 1=1"""
        params = []
        if item_code:
            sql += " AND item_code = %s"
            params.append(item_code)
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT 200"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"fmea_id": r[0], "fmea_code": r[1], "fmea_type": r[2],
                 "item_code": r[3], "process_code": r[4], "title": r[5],
                 "status": r[6], "created_by": r[7],
                 "created_at": r[8].isoformat() if r[8] else None}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_fmea_detail(fmea_id: int) -> dict:
    """FMEA 상세 (항목 포함)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT fmea_id, fmea_code, fmea_type, item_code, process_code,
                      title, team_members, status, created_by, created_at
               FROM fmea WHERE fmea_id = %s""", (fmea_id,))
        f = cursor.fetchone()
        if not f:
            cursor.close()
            return {"error": "FMEA를 찾을 수 없습니다."}

        cursor.execute(
            """SELECT fmea_item_id, process_step, failure_mode, failure_effect,
                      failure_cause, severity, occurrence, detection, rpn,
                      recommended_action, action_taken, action_owner, action_due,
                      new_severity, new_occurrence, new_detection, new_rpn, status
               FROM fmea_items WHERE fmea_id = %s ORDER BY rpn DESC""",
            (fmea_id,),
        )
        items = cursor.fetchall()
        cursor.close()

        high_rpn = [i for i in items if i[8] and i[8] >= 100]

        return {
            "fmea_id": f[0], "fmea_code": f[1], "fmea_type": f[2],
            "item_code": f[3], "process_code": f[4], "title": f[5],
            "team_members": f[6], "status": f[7],
            "items": [
                {"fmea_item_id": i[0], "process_step": i[1],
                 "failure_mode": i[2], "failure_effect": i[3],
                 "failure_cause": i[4], "severity": i[5],
                 "occurrence": i[6], "detection": i[7], "rpn": i[8],
                 "recommended_action": i[9], "action_taken": i[10],
                 "action_owner": i[11],
                 "action_due": i[12].isoformat() if i[12] else None,
                 "new_severity": i[13], "new_occurrence": i[14],
                 "new_detection": i[15], "new_rpn": i[16], "status": i[17]}
                for i in items
            ],
            "summary": {
                "total_items": len(items),
                "high_rpn_count": len(high_rpn),
                "max_rpn": max((i[8] for i in items), default=0),
                "avg_rpn": round(sum(i[8] for i in items if i[8]) / len(items), 1)
                           if items else 0,
            },
        }
    except Exception as e:
        log.error("FMEA 상세 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
