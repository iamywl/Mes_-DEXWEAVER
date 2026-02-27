"""FN-008~009: BOM (Bill of Materials) management module."""

from api_modules.database import db_connection, get_conn, release_conn


async def list_bom() -> dict:
    """List all BOM entries with parent/child item details."""
    try:
        with db_connection() as conn:
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


async def where_used(item_code: str) -> dict:
    """FN-006: Recursive reverse BOM explosion (역전개).

    Walks up the BOM tree to find all ancestor items that directly
    or indirectly use the given item as a component.
    Each result includes a 'level' field (1 = direct parent, 2+ = grandparent).
    """
    try:
        with db_connection() as conn:
            if not conn:
                return {"error": "Database connection failed."}
            cursor = conn.cursor()

            all_parents = []
            visited = set()

            def _walk_up(code, level):
                cursor.execute(
                    "SELECT b.bom_id, b.parent_item, p.name AS parent_name, "
                    "p.category AS parent_category, b.qty_per_unit, b.loss_rate "
                    "FROM bom b "
                    "JOIN items p ON b.parent_item = p.item_code "
                    "WHERE b.child_item = %s "
                    "ORDER BY b.parent_item",
                    (code,),
                )
                rows = cursor.fetchall()
                for r in rows:
                    parent = r[1]
                    if parent in visited:
                        continue
                    visited.add(parent)
                    all_parents.append({
                        "bom_id": r[0], "parent_item": parent, "parent_name": r[2],
                        "parent_category": r[3], "qty_per_unit": float(r[4]),
                        "loss_rate": float(r[5]), "level": level,
                    })
                    _walk_up(parent, level + 1)

            _walk_up(item_code, 1)
            cursor.close()
            return {"item_code": item_code, "used_in": all_parents, "count": len(all_parents)}
    except Exception as e:
        return {"error": str(e), "used_in": [], "count": 0}


async def bom_summary() -> dict:
    """Summary statistics for BOM data."""
    try:
        with db_connection() as conn:
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


def _check_circular(cursor, parent: str, child: str) -> bool:
    """Recursive circular reference check: A→B→C→A detection."""
    visited = set()

    def _walk(current):
        if current == parent:
            return True
        if current in visited:
            return False
        visited.add(current)
        cursor.execute(
            "SELECT child_item FROM bom WHERE parent_item = %s",
            (current,),
        )
        for (next_child,) in cursor.fetchall():
            if _walk(next_child):
                return True
        return False

    return _walk(child)


async def create_bom(data: dict) -> dict:
    """FN-008: Register a BOM entry with recursive circular reference check."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}

        cursor = conn.cursor()

        parent = data.get("parent_item", "").strip()
        child = data.get("child_item", "").strip()

        if not parent or not child:
            return {"error": "모품목과 자품목 코드는 필수입니다."}

        # Direct circular reference check
        if parent == child:
            return {"error": "모품목과 자품목이 동일할 수 없습니다."}

        # Recursive circular reference check (A→B→C→A)
        if _check_circular(cursor, parent, child):
            return {"error": f"순환참조가 감지되었습니다. {child}의 하위에 이미 {parent}가 존재합니다."}

        qty = data.get("qty_per_unit", 1)
        loss = data.get("loss_rate", 0)
        if qty <= 0:
            return {"error": "소요량은 0보다 커야 합니다."}

        cursor.execute(
            "INSERT INTO bom (parent_item, child_item, qty_per_unit, loss_rate) "
            "VALUES (%s, %s, %s, %s) RETURNING bom_id",
            (parent, child, qty, loss),
        )
        bom_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"bom_id": bom_id, "success": True}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "BOM 등록 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def update_bom(bom_id: int, data: dict) -> dict:
    """FN-008: Update a BOM entry."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT parent_item, child_item FROM bom WHERE bom_id = %s", (bom_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "BOM 항목을 찾을 수 없습니다."}

        new_child = data.get("child_item", row[1]).strip()
        parent = row[0]

        if parent == new_child:
            return {"error": "모품목과 자품목이 동일할 수 없습니다."}

        if new_child != row[1] and _check_circular(cursor, parent, new_child):
            return {"error": f"순환참조가 감지되었습니다."}

        sets = []
        params = []
        for field, col in [("child_item", "child_item"), ("qty_per_unit", "qty_per_unit"),
                           ("loss_rate", "loss_rate")]:
            if field in data:
                sets.append(f"{col} = %s")
                params.append(data[field])

        if not sets:
            return {"error": "수정할 항목이 없습니다."}

        params.append(bom_id)
        cursor.execute(f"UPDATE bom SET {', '.join(sets)} WHERE bom_id = %s", params)
        conn.commit()
        cursor.close()
        return {"success": True, "bom_id": bom_id}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "BOM 수정 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def delete_bom(bom_id: int) -> dict:
    """FN-008: Delete a BOM entry."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bom WHERE bom_id = %s", (bom_id,))
        if cursor.rowcount == 0:
            return {"error": "BOM 항목을 찾을 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True, "deleted": bom_id}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "BOM 삭제 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def explode_bom(item_code: str, qty: float = 1) -> dict:
    """FN-009: Explode BOM tree recursively."""
    try:
        with db_connection() as conn:
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
