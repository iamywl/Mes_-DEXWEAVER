"""REQ-073: 설계변경관리(ECM) — ECR→ECN→ECO 워크플로우."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# ECR→ECN→ECO: SUBMITTED→UNDER_REVIEW→APPROVED→ECN_ISSUED→ECO_COMPLETE
VALID_TRANSITIONS = {
    "SUBMITTED": ["UNDER_REVIEW", "REJECTED"],
    "UNDER_REVIEW": ["APPROVED", "REJECTED"],
    "APPROVED": ["ECN_ISSUED"],
    "ECN_ISSUED": ["ECO_COMPLETE"],
}


async def create_ecr(data: dict) -> dict:
    """ECR(설계변경요청) 생성."""
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
        cursor.execute("SELECT COUNT(*) FROM ecm_requests WHERE ecr_code LIKE %s",
                       (f"ECR-{today}-%",))
        seq = (cursor.fetchone()[0] or 0) + 1
        ecr_code = f"ECR-{today}-{seq:03d}"

        import json
        cursor.execute(
            """INSERT INTO ecm_requests
               (ecr_code, title, description, change_type, priority,
                affected_items, impact_analysis, requested_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING ecr_id""",
            (ecr_code, title, data.get("description"),
             data.get("change_type", "DESIGN"),
             data.get("priority", "NORMAL"),
             json.dumps(data.get("affected_items", [])),
             data.get("impact_analysis"),
             data.get("requested_by")),
        )
        ecr_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "ecr_id": ecr_id, "ecr_code": ecr_code}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("ECR 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def transition_ecr(ecr_id: int, data: dict) -> dict:
    """ECR 상태 전이."""
    new_status = data.get("status", "").strip()

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM ecm_requests WHERE ecr_id = %s", (ecr_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": "ECR을 찾을 수 없습니다."}

        current = row[0]
        if new_status not in VALID_TRANSITIONS.get(current, []):
            cursor.close()
            return {"error": f"{current} → {new_status} 전이 불가"}

        sets = ["status = %s"]
        params = [new_status]
        if new_status == "APPROVED" and data.get("approved_by"):
            sets.append("approved_by = %s")
            params.append(data["approved_by"])

        params.append(ecr_id)
        cursor.execute(
            f"UPDATE ecm_requests SET {', '.join(sets)} WHERE ecr_id = %s",
            tuple(params),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "ecr_id": ecr_id,
                "prev": current, "new": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_ecr_list(status: str = None, change_type: str = None) -> dict:
    """ECR 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = """SELECT ecr_id, ecr_code, title, change_type, priority,
                        status, affected_items, requested_by, created_at
                 FROM ecm_requests WHERE 1=1"""
        params = []
        if status:
            sql += " AND status = %s"
            params.append(status)
        if change_type:
            sql += " AND change_type = %s"
            params.append(change_type)
        sql += " ORDER BY created_at DESC LIMIT 200"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"ecr_id": r[0], "ecr_code": r[1], "title": r[2],
                 "change_type": r[3], "priority": r[4], "status": r[5],
                 "affected_items": r[6], "requested_by": r[7],
                 "created_at": r[8].isoformat() if r[8] else None}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
