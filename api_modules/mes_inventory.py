"""FN-029~031: Inventory management (in/out/status) + LOT traceability."""

from datetime import date

from api_modules.database import get_conn, release_conn


def _slip_no(prefix: str, cur) -> str:
    today = date.today().strftime("%Y%m%d")
    cur.execute(
        "SELECT COUNT(*) FROM inventory_transactions "
        "WHERE slip_no LIKE %s",
        (f"{prefix}-{today}-%",),
    )
    seq = cur.fetchone()[0] + 1
    return f"{prefix}-{today}-{seq:03d}"


async def inventory_in(data: dict) -> dict:
    """FN-029: Receive goods (입고)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()
        item_code = data["item_code"]
        qty = data["qty"]
        wh = data.get("warehouse", "WH01")
        loc = data.get("location")
        today = date.today().strftime("%Y%m%d")

        # Auto-generate lot_no
        cur.execute(
            "SELECT COUNT(*) FROM inventory "
            "WHERE lot_no LIKE %s",
            (f"LOT-{today}-%",),
        )
        lot_seq = cur.fetchone()[0] + 1
        lot_no = f"LOT-{today}-{lot_seq:03d}"
        slip_no = _slip_no("IN", cur)

        # Upsert inventory
        cur.execute(
            "INSERT INTO inventory (item_code, lot_no, qty, warehouse, location) "
            "VALUES (%s,%s,%s,%s,%s) "
            "ON CONFLICT (item_code, lot_no, warehouse) "
            "DO UPDATE SET qty = inventory.qty + EXCLUDED.qty",
            (item_code, lot_no, qty, wh, loc),
        )
        cur.execute(
            "INSERT INTO inventory_transactions "
            "(slip_no, item_code, lot_no, qty, tx_type, warehouse, "
            "location, supplier) "
            "VALUES (%s,%s,%s,%s,'IN',%s,%s,%s)",
            (slip_no, item_code, lot_no, qty, wh, loc,
             data.get("supplier")),
        )
        conn.commit()
        cur.close()
        return {"lot_no": lot_no, "slip_no": slip_no}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def inventory_out(data: dict) -> dict:
    """FN-030: Issue goods (출고) with FIFO + full transaction info."""
    VALID_OUT_TYPES = {"OUT", "SHIP", "SCRAP", "RETURN"}
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cur = conn.cursor()

        item_code = data.get("item_code", "").strip()
        if not item_code:
            return {"error": "품목코드는 필수입니다."}
        qty_needed = data.get("qty", 0)
        if qty_needed <= 0:
            return {"error": "출고 수량은 0보다 커야 합니다."}

        out_type = data.get("out_type", "OUT").upper()
        if out_type not in VALID_OUT_TYPES:
            return {"error": f"유효하지 않은 출고유형입니다. 허용: {', '.join(VALID_OUT_TYPES)}"}

        slip_no = _slip_no("OUT", cur)

        # FIFO: oldest lots first
        cur.execute(
            "SELECT inv_id, lot_no, qty, warehouse FROM inventory "
            "WHERE item_code = %s AND qty > 0 "
            "ORDER BY created_at ASC",
            (item_code,),
        )
        lots = cur.fetchall()
        remaining = qty_needed
        lots_used = []

        for inv_id, lot_no, lot_qty, wh in lots:
            if remaining <= 0:
                break
            use = min(remaining, lot_qty)
            cur.execute(
                "UPDATE inventory SET qty = qty - %s WHERE inv_id = %s",
                (use, inv_id),
            )
            lots_used.append({"lot_no": lot_no, "qty": use, "warehouse": wh})
            remaining -= use

        if remaining > 0:
            conn.rollback()
            cur.close()
            return {"error": f"재고 부족. 부족 수량: {remaining}"}

        # Record full transaction with lot_no and warehouse
        first_lot = lots_used[0] if lots_used else {}
        cur.execute(
            "INSERT INTO inventory_transactions "
            "(slip_no, item_code, lot_no, qty, tx_type, warehouse, ref_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (slip_no, item_code,
             first_lot.get("lot_no"),
             qty_needed, out_type,
             first_lot.get("warehouse"),
             data.get("ref_id")),
        )
        conn.commit()
        cur.close()
        return {"slip_no": slip_no, "lots_used": lots_used}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "출고 처리 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_inventory(warehouse: str = None,
                        category: str = None) -> dict:
    """FN-031: Current inventory status."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"items": []}
        cur = conn.cursor()

        where = []
        params = []
        if warehouse:
            where.append("inv.warehouse = %s")
            params.append(warehouse)
        if category:
            where.append("i.category = %s")
            params.append(category)
        wsql = "WHERE " + " AND ".join(where) if where else ""

        # available = stock - reserved (진행중 작업지시에 할당된 수량)
        cur.execute(
            f"SELECT i.item_code, i.name, "
            f"COALESCE(SUM(inv.qty),0) AS stock, "
            f"i.safety_stock, "
            f"COALESCE(("
            f"  SELECT SUM(wo.plan_qty) FROM work_orders wo "
            f"  WHERE wo.item_code = i.item_code AND wo.status IN ('WAIT','WORKING')"
            f"),0) AS reserved "
            f"FROM items i "
            f"LEFT JOIN inventory inv ON i.item_code = inv.item_code "
            f"{'AND inv.warehouse = %s' if warehouse else ''} "
            f"{'WHERE i.category = %s' if category else ''} "
            f"GROUP BY i.item_code, i.name, i.safety_stock "
            f"ORDER BY i.item_code",
            ([warehouse] if warehouse else []) +
            ([category] if category else []),
        )
        rows = cur.fetchall()
        cur.close()

        items = []
        for r in rows:
            stock, safety, reserved = r[2], r[3], r[4]
            available = max(0, stock - reserved)
            if stock <= 0:
                st = "OUT"
            elif stock < safety:
                st = "LOW"
            else:
                st = "NORMAL"
            items.append({
                "item_code": r[0], "name": r[1],
                "stock": stock, "available": available,
                "safety": safety, "status": st,
            })
        return {"items": items}
    except Exception:
        return {"error": "재고 현황 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def trace_lot(lot_no: str) -> dict:
    """LOT Traceability: 완제품 LOT → 원자재 LOT → 설비 → 작업자 → 공정시간 역추적.

    GS인증 KS X 9003: LOT 추적성 데이터 연결 성공률 100% 요구.
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cur = conn.cursor()

        # 1. LOT의 기본정보 (재고)
        cur.execute(
            "SELECT inv.item_code, i.name, inv.qty, inv.warehouse, "
            "inv.location, inv.created_at "
            "FROM inventory inv "
            "JOIN items i ON inv.item_code = i.item_code "
            "WHERE inv.lot_no = %s",
            (lot_no,),
        )
        inv_rows = cur.fetchall()
        lot_info = [
            {"item_code": r[0], "item_name": r[1], "qty": r[2],
             "warehouse": r[3], "location": r[4],
             "created_at": str(r[5]) if r[5] else None}
            for r in inv_rows
        ]

        # 2. 입출고 이력
        cur.execute(
            "SELECT slip_no, item_code, qty, tx_type, warehouse, "
            "location, supplier, ref_id, created_at "
            "FROM inventory_transactions WHERE lot_no = %s "
            "ORDER BY created_at",
            (lot_no,),
        )
        tx_rows = cur.fetchall()
        transactions = [
            {"slip_no": r[0], "item_code": r[1], "qty": r[2],
             "type": r[3], "warehouse": r[4], "location": r[5],
             "supplier": r[6], "ref_id": r[7],
             "time": str(r[8]) if r[8] else None}
            for r in tx_rows
        ]

        # 3. 관련 작업지시/실적 (ref_id로 연결)
        work_info = []
        for tx in transactions:
            if tx.get("ref_id") and tx["ref_id"].startswith("WO-"):
                cur.execute(
                    "SELECT wo.wo_id, wo.item_code, i.name, "
                    "wo.equip_code, wo.work_date, wo.status "
                    "FROM work_orders wo "
                    "JOIN items i ON wo.item_code = i.item_code "
                    "WHERE wo.wo_id = %s",
                    (tx["ref_id"],),
                )
                wo = cur.fetchone()
                if wo:
                    cur.execute(
                        "SELECT wr.worker_id, wr.good_qty, wr.defect_qty, "
                        "wr.start_time, wr.end_time "
                        "FROM work_results wr WHERE wr.wo_id = %s",
                        (wo[0],),
                    )
                    results = cur.fetchall()
                    work_info.append({
                        "wo_id": wo[0], "item_code": wo[1],
                        "item_name": wo[2], "equip_code": wo[3],
                        "work_date": str(wo[4]), "status": wo[5],
                        "results": [
                            {"worker_id": r[0], "good_qty": r[1],
                             "defect_qty": r[2],
                             "start_time": str(r[3]) if r[3] else None,
                             "end_time": str(r[4]) if r[4] else None}
                            for r in results
                        ],
                    })

        # 4. 품질검사 이력
        cur.execute(
            "SELECT ins.inspection_id, ins.inspect_type, ins.judgment, "
            "ins.inspector_id, ins.inspected_at "
            "FROM inspections ins WHERE ins.lot_no = %s "
            "ORDER BY ins.inspected_at",
            (lot_no,),
        )
        inspections = [
            {"inspection_id": r[0], "type": r[1], "judgment": r[2],
             "inspector_id": r[3],
             "time": str(r[4]) if r[4] else None}
            for r in cur.fetchall()
        ]

        cur.close()
        return {
            "lot_no": lot_no,
            "inventory": lot_info,
            "transactions": transactions,
            "work_orders": work_info,
            "inspections": inspections,
            "trace_complete": True,
        }
    except Exception:
        return {"error": "LOT 추적 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
