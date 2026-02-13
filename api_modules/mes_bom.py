"""FN-008~009: BOM (Bill of Materials) management module."""

from api_modules.database import get_conn, release_conn


async def list_bom() -> dict:
    """List all BOM entries with parent/child item details."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}
        cursor = conn.cursor()
        cursor.execute(
            "SELECT b.bom_id, b.parent_item, p.name AS parent_name, "
            "b.child_item, c.name AS child_name, c.category AS child_category, "
            "b.qty_per_unit, b.loss_rate "
            "FROM bom b "
            "JOIN items p ON b.parent_item = p.item_code "
            "JOIN items c ON b.child_item = c.item_code "
            "ORDER BY b.parent_item, b.child_item"
        )
        rows = cursor.fetchall()
        cursor.close()
        entries = [
            {
                "bom_id": r[0], "parent_item": r[1], "parent_name": r[2],
                "child_item": r[3], "child_name": r[4], "child_category": r[5],
                "qty_per_unit": float(r[6]), "loss_rate": float(r[7]),
            }
            for r in rows
        ]
        return {"entries": entries, "total": len(entries)}
    except Exception as e:
        return {"error": str(e), "entries": [], "total": 0}
    finally:
        if conn:
            release_conn(conn)


async def where_used(item_code: str) -> dict:
    """Find all parent items that use the given item as a component."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}
        cursor = conn.cursor()
        cursor.execute(
            "SELECT b.bom_id, b.parent_item, p.name AS parent_name, "
            "p.category AS parent_category, b.qty_per_unit, b.loss_rate "
            "FROM bom b "
            "JOIN items p ON b.parent_item = p.item_code "
            "WHERE b.child_item = %s "
            "ORDER BY b.parent_item",
            (item_code,),
        )
        rows = cursor.fetchall()
        cursor.close()
        parents = [
            {
                "bom_id": r[0], "parent_item": r[1], "parent_name": r[2],
                "parent_category": r[3], "qty_per_unit": float(r[4]),
                "loss_rate": float(r[5]),
            }
            for r in rows
        ]
        return {"item_code": item_code, "used_in": parents, "count": len(parents)}
    except Exception as e:
        return {"error": str(e), "used_in": [], "count": 0}
    finally:
        if conn:
            release_conn(conn)


async def bom_summary() -> dict:
    """Summary statistics for BOM data."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bom")
        total_entries = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT parent_item) FROM bom")
        parent_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT child_item) FROM bom")
        child_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT b.parent_item, p.name, COUNT(*) AS comp_count "
            "FROM bom b JOIN items p ON b.parent_item = p.item_code "
            "GROUP BY b.parent_item, p.name ORDER BY comp_count DESC LIMIT 10"
        )
        top_parents = [
            {"item_code": r[0], "name": r[1], "component_count": r[2]}
            for r in cursor.fetchall()
        ]
        cursor.close()
        return {
            "total_entries": total_entries,
            "parent_count": parent_count,
            "child_count": child_count,
            "top_parents": top_parents,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


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
