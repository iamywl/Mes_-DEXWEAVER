"""REQ-056: 출하판정 (Shipment Disposition)."""

import logging
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_disposition(data: dict, user_id: str = None) -> dict:
    """출하판정 등록.

    body: { "lot_no", "item_code", "decision": "ACCEPT|REJECT|CONDITIONAL|HOLD", "reason" }
    """
    lot_no = data.get("lot_no", "").strip()
    decision = data.get("decision", "").strip()

    if not lot_no or not decision:
        return {"error": "lot_no, decision은 필수입니다."}
    if decision not in ("ACCEPT", "REJECT", "CONDITIONAL", "HOLD"):
        return {"error": f"decision은 ACCEPT/REJECT/CONDITIONAL/HOLD 중 하나여야 합니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT COUNT(*) FROM shipment_disposition WHERE disp_id LIKE %s",
            (f"DSP-{today}-%",),
        )
        seq = (cursor.fetchone()[0] or 0) + 1
        disp_id = f"DSP-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO shipment_disposition
               (disp_id, lot_no, item_code, decision, reason, inspector_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (disp_id, lot_no, data.get("item_code"),
             decision, data.get("reason", ""), user_id),
        )

        # REJECT이면 재고 HOLD 처리
        if decision == "REJECT":
            cursor.execute(
                "UPDATE inventory SET status = 'HOLD' WHERE lot_no = %s AND status = 'NORMAL'",
                (lot_no,),
            )

        conn.commit()
        cursor.close()
        return {"success": True, "disp_id": disp_id, "decision": decision}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("출하판정 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_dispositions(lot_no: str = None, decision: str = None) -> dict:
    """출하판정 이력 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT disp_id, lot_no, item_code, decision, reason,
                        inspector_id, decided_at
                 FROM shipment_disposition WHERE 1=1"""
        params = []
        if lot_no:
            sql += " AND lot_no = %s"
            params.append(lot_no)
        if decision:
            sql += " AND decision = %s"
            params.append(decision)
        sql += " ORDER BY decided_at DESC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "disp_id": r[0], "lot_no": r[1], "item_code": r[2],
                    "decision": r[3], "reason": r[4], "inspector_id": r[5],
                    "decided_at": r[6].isoformat() if r[6] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
