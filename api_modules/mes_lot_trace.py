"""FN-048: LOT 계보 추적 — Forward/Backward 추적."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def trace_genealogy(lot_no: str, direction: str = "both",
                            max_depth: int = 10) -> dict:
    """FN-048: LOT 계보 추적 (Forward/Backward)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # LOT 기본 정보 조회
        cursor.execute(
            """SELECT inv.item_code, inv.qty, inv.warehouse, inv.location, i.name
               FROM inventory inv
               JOIN items i ON inv.item_code = i.item_code
               WHERE inv.lot_no = %s""",
            (lot_no,))
        lot_info = cursor.fetchone()
        if not lot_info:
            cursor.close()
            return {"error": f"LOT {lot_no}를 찾을 수 없습니다."}

        result = {
            "lot_no": lot_no,
            "item_code": lot_info[0],
            "item_name": lot_info[4],
            "qty": lot_info[1],
            "warehouse": lot_info[2],
            "location": lot_info[3],
        }

        # Forward 추적: 원자재 → 완제품
        if direction in ("forward", "both"):
            result["forward"] = _trace_forward(cursor, lot_no, max_depth)

        # Backward 추적: 완제품 → 원자재
        if direction in ("backward", "both"):
            result["backward"] = _trace_backward(cursor, lot_no, max_depth)

        # 리콜 시뮬레이션
        if direction in ("forward", "both"):
            result["recall_impact"] = _recall_simulation(cursor, lot_no, result.get("forward", []))

        cursor.close()
        return result
    except Exception as e:
        log.error("LOT trace error: %s", e)
        return {"error": "LOT 추적 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


def _trace_forward(cursor, lot_no, max_depth, depth=0):
    """Forward: 이 LOT가 사용된 작업 → 완성품 LOT 추적."""
    if depth >= max_depth:
        return []

    # 이 LOT가 출고(OUT)된 작업지시 조회
    cursor.execute(
        """SELECT DISTINCT it.ref_id
           FROM inventory_transactions it
           WHERE it.lot_no = %s AND it.tx_type = 'OUT' AND it.ref_id IS NOT NULL""",
        (lot_no,))
    ref_ids = [r[0] for r in cursor.fetchall()]

    children = []
    for ref_id in ref_ids:
        # ref_id가 작업지시 ID인 경우
        cursor.execute(
            """SELECT wo.wo_id, wo.item_code, i.name, wr.good_qty
               FROM work_orders wo
               JOIN items i ON wo.item_code = i.item_code
               LEFT JOIN work_results wr ON wo.wo_id = wr.wo_id
               WHERE wo.wo_id = %s""",
            (ref_id,))
        wo_rows = cursor.fetchall()

        for wo_id, item_code, item_name, good_qty in wo_rows:
            # 이 작업에서 생산된 완성품 LOT 조회
            cursor.execute(
                """SELECT lot_no, qty
                   FROM inventory_transactions
                   WHERE ref_id = %s AND tx_type = 'IN' AND item_code = %s""",
                (wo_id, item_code))
            output_lots = cursor.fetchall()

            for out_lot, out_qty in output_lots:
                child = {
                    "lot_no": out_lot,
                    "item_code": item_code,
                    "item_name": item_name,
                    "qty": out_qty,
                    "via_wo": wo_id,
                    "children": _trace_forward(cursor, out_lot, max_depth, depth + 1),
                }
                children.append(child)

    return children


def _trace_backward(cursor, lot_no, max_depth, depth=0):
    """Backward: 이 LOT를 만든 원자재 LOT 추적."""
    if depth >= max_depth:
        return []

    # 이 LOT가 입고(IN)된 작업지시 조회
    cursor.execute(
        """SELECT ref_id, item_code
           FROM inventory_transactions
           WHERE lot_no = %s AND tx_type = 'IN' AND ref_id IS NOT NULL""",
        (lot_no,))
    in_txs = cursor.fetchall()

    parents = []
    for ref_id, _ in in_txs:
        # 작업지시에서 사용된 원자재 LOT 조회
        cursor.execute(
            """SELECT it.lot_no, it.item_code, i.name, it.qty
               FROM inventory_transactions it
               JOIN items i ON it.item_code = i.item_code
               WHERE it.ref_id = %s AND it.tx_type = 'OUT'""",
            (ref_id,))
        mat_rows = cursor.fetchall()

        for mat_lot, mat_item, mat_name, mat_qty in mat_rows:
            parent = {
                "lot_no": mat_lot,
                "item_code": mat_item,
                "item_name": mat_name,
                "qty": mat_qty,
                "via_wo": ref_id,
                "parents": _trace_backward(cursor, mat_lot, max_depth, depth + 1),
            }
            parents.append(parent)

    return parents


def _recall_simulation(cursor, lot_no, forward_tree):
    """리콜 시뮬레이션: 영향 LOT 수, 품목, 수량 산출."""
    affected_lots = set()
    affected_items = {}

    def _collect(nodes):
        for node in nodes:
            affected_lots.add(node["lot_no"])
            ic = node["item_code"]
            affected_items[ic] = affected_items.get(ic, 0) + (node.get("qty") or 0)
            _collect(node.get("children", []))

    _collect(forward_tree)

    return {
        "source_lot": lot_no,
        "affected_lot_count": len(affected_lots),
        "affected_item_count": len(affected_items),
        "affected_items": [
            {"item_code": k, "total_qty": v} for k, v in affected_items.items()
        ],
    }
