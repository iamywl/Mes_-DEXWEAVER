"""FN-041~043: CAPA 프로세스 — 등록, 상태 전이, 목록 조회."""

import logging
from datetime import date
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# 상태 전이 규칙: {현재 상태: [허용 다음 상태]}
TRANSITIONS = {
    "OPEN": ["INVESTIGATION"],
    "INVESTIGATION": ["ACTION", "REJECTED"],
    "ACTION": ["VERIFICATION"],
    "VERIFICATION": ["CLOSED", "OPEN"],  # OPEN으로 돌아가면 재작업
    "CLOSED": [],
    "REJECTED": ["OPEN"],
}


async def create_capa(data: dict) -> dict:
    """FN-041: CAPA 등록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        title = data.get("title")
        capa_type = data.get("capa_type", "CORRECTIVE")
        if not title:
            cursor.close()
            return {"error": "title은 필수입니다."}
        if capa_type not in ("CORRECTIVE", "PREVENTIVE"):
            cursor.close()
            return {"error": "capa_type은 CORRECTIVE 또는 PREVENTIVE여야 합니다."}

        # CAPA ID 생성
        date_part = date.today().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM capa WHERE capa_id LIKE %s",
                        (f"CAPA-{date_part}-%",))
        seq = cursor.fetchone()[0] + 1
        capa_id = f"CAPA-{date_part}-{seq:03d}"

        cursor.execute(
            """INSERT INTO capa (capa_id, capa_type, source_type, source_id,
                   title, description, priority, assigned_to, due_date, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (capa_id, capa_type,
             data.get("source_type"), data.get("source_id"),
             title, data.get("description"),
             data.get("priority", "MID"),
             data.get("assigned_to"), data.get("due_date"),
             data.get("created_by")))
        conn.commit()
        cursor.close()
        return {"success": True, "capa_id": capa_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("CAPA creation error: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def update_capa_status(capa_id: str, data: dict) -> dict:
    """FN-042: CAPA 워크플로우 상태 전이."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        new_status = data.get("status")
        if not new_status:
            cursor.close()
            return {"error": "status는 필수입니다."}

        cursor.execute("SELECT status FROM capa WHERE capa_id = %s", (capa_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": f"CAPA {capa_id}를 찾을 수 없습니다."}

        current = row[0]
        allowed = TRANSITIONS.get(current, [])
        if new_status not in allowed:
            cursor.close()
            return {"error": f"상태 전이 불가: {current} → {new_status} (허용: {allowed})"}

        # 상태 업데이트
        if new_status == "CLOSED":
            cursor.execute(
                "UPDATE capa SET status = %s, closed_at = NOW() WHERE capa_id = %s",
                (new_status, capa_id))
        else:
            cursor.execute(
                "UPDATE capa SET status = %s WHERE capa_id = %s",
                (new_status, capa_id))

        # 조치 이력 기록
        if data.get("action_type") and data.get("description"):
            cursor.execute(
                """INSERT INTO capa_actions (capa_id, action_type, description, result, performed_by)
                   VALUES (%s, %s, %s, %s, %s)""",
                (capa_id, data["action_type"], data["description"],
                 data.get("result"), data.get("performed_by")))

        conn.commit()
        cursor.close()
        return {"success": True, "capa_id": capa_id,
                "previous_status": current, "new_status": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("CAPA status update error: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_capa_list(status: str = None, capa_type: str = None,
                         assigned_to: str = None) -> dict:
    """FN-043: CAPA 목록/이력 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT c.capa_id, c.capa_type, c.source_type, c.source_id,
                        c.title, c.status, c.priority, c.assigned_to, c.due_date,
                        c.closed_at, c.created_by, c.created_at,
                        (SELECT COUNT(*) FROM capa_actions ca WHERE ca.capa_id = c.capa_id) as action_count
                 FROM capa c WHERE 1=1"""
        params = []
        if status:
            sql += " AND c.status = %s"
            params.append(status)
        if capa_type:
            sql += " AND c.capa_type = %s"
            params.append(capa_type)
        if assigned_to:
            sql += " AND c.assigned_to = %s"
            params.append(assigned_to)
        sql += " ORDER BY c.created_at DESC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        items = []
        for r in rows:
            items.append({
                "capa_id": r[0], "capa_type": r[1], "source_type": r[2],
                "source_id": r[3], "title": r[4], "status": r[5],
                "priority": r[6], "assigned_to": r[7],
                "due_date": str(r[8]) if r[8] else None,
                "closed_at": str(r[9]) if r[9] else None,
                "created_by": r[10],
                "created_at": str(r[11]) if r[11] else None,
                "action_count": r[12],
            })

        # 상태별 요약
        cursor.execute("SELECT status, COUNT(*) FROM capa GROUP BY status")
        summary = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.close()
        return {"items": items, "total": len(items), "summary": summary}
    except Exception as e:
        log.error("CAPA list error: %s", e)
        return {"error": "CAPA 목록 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
