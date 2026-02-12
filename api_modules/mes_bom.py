"""FN-008~009: BOM (Bill of Materials) management module."""

from api_modules.database import get_conn, release_conn


async def create_bom(data: dict) -> dict:
    """FN-008: Register a BOM entry."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        parent = data["parent_item"]
        child = data["child_item"]

        # Circular reference check
        if parent == child:
            return {"error": "Parent and child cannot be the same."}

        cursor.execute(
            "INSERT INTO bom (parent_item, child_item, qty_per_unit, loss_rate) "
            "VALUES (%s, %s, %s, %s) RETURNING bom_id",
            (parent, child,
             data.get("qty_per_unit", 1),
             data.get("loss_rate", 0)),
        )
        bom_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"bom_id": bom_id, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def explode_bom(item_code: str, qty: float = 1) -> dict:
    """FN-009: Explode BOM tree recursively."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        def _explode(parent, parent_qty, level):
            cursor.execute(
                "SELECT b.child_item, i.name, b.qty_per_unit, b.loss_rate "
                "FROM bom b JOIN items i ON b.child_item = i.item_code "
                "WHERE b.parent_item = %s",
                (parent,),
            )
            rows = cursor.fetchall()
            children = []
            for r in rows:
                required = float(r[2]) * parent_qty * (1 + float(r[3]) / 100)
                node = {
                    "level": level,
                    "item_code": r[0],
                    "item_name": r[1],
                    "qty_per_unit": float(r[2]),
                    "loss_rate": float(r[3]),
                    "required_qty": round(required, 2),
                    "children": _explode(r[0], required, level + 1),
                }
                children.append(node)
            return children

        tree = _explode(item_code, qty, 1)
        cursor.close()
        return {"item_code": item_code, "qty": qty, "tree": tree}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
