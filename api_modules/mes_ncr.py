"""REQ-054: 부적합품 관리 (NCR — Non-Conformance Report)."""

import logging
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# 상태 전이 규칙
_VALID_TRANSITIONS = {
    "DETECTED":    ["QUARANTINED"],
    "QUARANTINED": ["MRB_REVIEW"],
    "MRB_REVIEW":  ["DISPOSITION"],
    "DISPOSITION": ["CLOSED"],
}


async def create_ncr(data: dict, user_id: str = None) -> dict:
    """NCR 등록.

    body: { "title", "source", "lot_no", "item_code", "defect_code",
            "qty_affected", "description", "assigned_to" }
    """
    title = data.get("title", "").strip()
    if not title:
        return {"error": "title은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT COUNT(*) FROM ncr WHERE ncr_id LIKE %s",
            (f"NCR-{today}-%",),
        )
        seq = (cursor.fetchone()[0] or 0) + 1
        ncr_id = f"NCR-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO ncr
               (ncr_id, title, source, lot_no, item_code, defect_code,
                qty_affected, description, assigned_to, created_by, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'DETECTED')""",
            (ncr_id, title,
             data.get("source", "INSPECTION"),
             data.get("lot_no"), data.get("item_code"),
             data.get("defect_code"),
             data.get("qty_affected", 0),
             data.get("description", ""),
             data.get("assigned_to"),
             user_id),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "ncr_id": ncr_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("NCR 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_ncr_list(status: str = None, lot_no: str = None) -> dict:
    """NCR 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT ncr_id, title, source, lot_no, item_code, defect_code,
                        qty_affected, status, disposition, assigned_to,
                        created_by, created_at, closed_at
                 FROM ncr WHERE 1=1"""
        params = []
        if status:
            sql += " AND status = %s"
            params.append(status)
        if lot_no:
            sql += " AND lot_no = %s"
            params.append(lot_no)
        sql += " ORDER BY created_at DESC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        # 상태 요약
        status_summary = {}
        for r in rows:
            s = r[7]
            status_summary[s] = status_summary.get(s, 0) + 1

        return {
            "items": [
                {
                    "ncr_id": r[0], "title": r[1], "source": r[2],
                    "lot_no": r[3], "item_code": r[4], "defect_code": r[5],
                    "qty_affected": float(r[6]) if r[6] else 0,
                    "status": r[7], "disposition": r[8],
                    "assigned_to": r[9], "created_by": r[10],
                    "created_at": r[11].isoformat() if r[11] else None,
                    "closed_at": r[12].isoformat() if r[12] else None,
                }
                for r in rows
            ],
            "summary": status_summary,
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def update_ncr_disposition(ncr_id: str, data: dict) -> dict:
    """NCR 상태 전이 및 처분 결정.

    body: { "status": "QUARANTINED"|..., "disposition": "REWORK"|... }
    """
    new_status = data.get("status", "").strip()
    disposition = data.get("disposition")

    if not new_status:
        return {"error": "status는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM ncr WHERE ncr_id = %s", (ncr_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": f"NCR '{ncr_id}'를 찾을 수 없습니다."}

        current = row[0]
        allowed = _VALID_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            cursor.close()
            return {"error": f"'{current}' → '{new_status}' 전이는 허용되지 않습니다. 가능: {allowed}"}

        updates = ["status = %s"]
        params = [new_status]

        if disposition:
            updates.append("disposition = %s")
            params.append(disposition)
        if new_status == "CLOSED":
            updates.append("closed_at = NOW()")

        params.append(ncr_id)
        cursor.execute(
            f"UPDATE ncr SET {', '.join(updates)} WHERE ncr_id = %s",
            tuple(params),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "ncr_id": ncr_id, "status": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("NCR 상태 변경 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
