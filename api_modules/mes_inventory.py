"""FN-029~031: Inventory management (in/out/status)."""

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
    """FN-030: Issue goods (출고) with FIFO."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()
        item_code = data["item_code"]
        qty_needed = data["qty"]
        slip_no = _slip_no("OUT", cur)

        # FIFO: oldest lots first
        cur.execute(
            "SELECT inv_id, lot_no, qty FROM inventory "
            "WHERE item_code = %s AND qty > 0 "
            "ORDER BY created_at ASC",
            (item_code,),
        )
        lots = cur.fetchall()
        remaining = qty_needed
        lots_used = []

        for inv_id, lot_no, lot_qty in lots:
            if remaining <= 0:
                break
            use = min(remaining, lot_qty)
            cur.execute(
                "UPDATE inventory SET qty = qty - %s WHERE inv_id = %s",
                (use, inv_id),
            )
            lots_used.append({"lot_no": lot_no, "qty": use})
            remaining -= use

        if remaining > 0:
            conn.rollback()
            cur.close()
            return {"error": f"Insufficient stock. Short by {remaining}."}

        cur.execute(
            "INSERT INTO inventory_transactions "
            "(slip_no, item_code, qty, tx_type, ref_id) "
            "VALUES (%s,%s,%s,%s,%s)",
            (slip_no, item_code, qty_needed,
             data.get("out_type", "OUT"), data.get("ref_id")),
        )
        conn.commit()
        cur.close()
        return {"slip_no": slip_no, "lots_used": lots_used}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
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

        cur.execute(
            f"SELECT i.item_code, i.name, "
            f"COALESCE(SUM(inv.qty),0) AS stock, "
            f"i.safety_stock "
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
            stock, safety = r[2], r[3]
            if stock <= 0:
                st = "OUT"
            elif stock < safety:
                st = "LOW"
            else:
                st = "NORMAL"
            items.append({
                "item_code": r[0], "name": r[1],
                "stock": stock, "available": stock,
                "safety": safety, "status": st,
            })
        return {"items": items}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
