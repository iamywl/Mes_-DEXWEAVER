"""REQ-066: 자동디스패칭/자재역산 — 스케줄→작업지시, BOM Backflush."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def auto_dispatch(plan_id: int = None) -> dict:
    """스케줄링 결과 → 작업지시 자동 생성."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # CONFIRMED 상태 생산계획 조회
        sql = """SELECT plan_id, item_code, plan_qty, line_code, start_date, end_date
                 FROM production_plans WHERE status = 'CONFIRMED'"""
        params = []
        if plan_id:
            sql += " AND plan_id = %s"
            params.append(plan_id)
        sql += " ORDER BY start_date"
        cursor.execute(sql, tuple(params))
        plans = cursor.fetchall()

        if not plans:
            cursor.close()
            return {"info": "디스패칭 대상 계획이 없습니다.", "created": 0}

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")

        created = []
        for p in plans:
            pid, item_code, plan_qty, line_code, start_d, end_d = p

            # 이미 작업지시가 있는지 확인
            cursor.execute(
                "SELECT COUNT(*) FROM work_orders WHERE plan_id = %s",
                (pid,),
            )
            if cursor.fetchone()[0] > 0:
                continue

            # WO 코드 생성
            cursor.execute("SELECT COUNT(*) FROM work_orders WHERE wo_code LIKE %s",
                           (f"WO-{today}-%",))
            seq = (cursor.fetchone()[0] or 0) + 1
            wo_code = f"WO-{today}-{seq:03d}"

            cursor.execute(
                """INSERT INTO work_orders
                   (wo_code, plan_id, item_code, order_qty, line_code,
                    start_date, end_date, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,'WAITING')""",
                (wo_code, pid, item_code, plan_qty, line_code, start_d, end_d),
            )
            created.append({"wo_code": wo_code, "item_code": item_code,
                            "qty": plan_qty})

        conn.commit()
        cursor.close()
        return {"success": True, "created": len(created), "work_orders": created}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("자동 디스패칭 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def backflush(wo_code: str, good_qty: int) -> dict:
    """BOM 기반 자재 역산 소비 (Backflush)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 작업지시 조회
        cursor.execute(
            "SELECT item_code FROM work_orders WHERE wo_code = %s",
            (wo_code,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": "작업지시를 찾을 수 없습니다."}
        parent_item = row[0]

        # BOM 전개 (1 level)
        cursor.execute(
            """SELECT child_item, qty_per_unit, loss_rate
               FROM bom WHERE parent_item = %s AND is_active = TRUE""",
            (parent_item,),
        )
        bom_rows = cursor.fetchall()
        if not bom_rows:
            cursor.close()
            return {"info": "BOM이 없어 역산할 자재가 없습니다."}

        consumed = []
        for child_item, qty_per, loss_rate in bom_rows:
            lr = float(loss_rate or 0)
            consume_qty = round(good_qty * float(qty_per) * (1 + lr / 100), 4)

            # 재고 차감
            cursor.execute(
                """UPDATE inventory SET current_qty = current_qty - %s
                   WHERE item_code = %s AND current_qty >= %s""",
                (consume_qty, child_item, consume_qty),
            )
            deducted = cursor.rowcount > 0

            # 출고 트랜잭션
            cursor.execute(
                """INSERT INTO inventory_transactions
                   (item_code, tx_type, qty, ref_code, description)
                   VALUES (%s, 'OUT', %s, %s, %s)""",
                (child_item, consume_qty, wo_code,
                 f"Backflush: {parent_item} x {good_qty}"),
            )
            consumed.append({"item_code": child_item, "qty": consume_qty,
                             "deducted": deducted})

        conn.commit()
        cursor.close()
        return {"success": True, "wo_code": wo_code,
                "parent_item": parent_item, "consumed": consumed}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("Backflush 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
