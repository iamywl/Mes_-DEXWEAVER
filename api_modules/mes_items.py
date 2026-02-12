"""FN-004~007: Item master management module."""

from api_modules.database import get_conn, release_conn


async def create_item(data: dict) -> dict:
    """FN-004: Register a new item with auto-generated code."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Auto-generate item_code: ITM-00001
        cursor.execute(
            "SELECT item_code FROM items ORDER BY item_code DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row and row[0].startswith("ITM-"):
            seq = int(row[0].split("-")[1]) + 1
        else:
            cursor.execute("SELECT COUNT(*) FROM items")
            seq = cursor.fetchone()[0] + 1
        item_code = f"ITM-{seq:05d}"

        cursor.execute(
            "INSERT INTO items (item_code, name, category, unit, spec, safety_stock) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                item_code,
                data["name"],
                data.get("category", "RAW"),
                data.get("unit", "EA"),
                data.get("spec"),
                data.get("safety_stock", 0),
            ),
        )
        conn.commit()
        cursor.close()
        return {"item_code": item_code, "created_at": "now"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_items(keyword: str = None, category: str = None,
                    page: int = 1, size: int = 20) -> dict:
    """FN-005: List items with search and pagination."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"items": [], "total": 0, "page": page}

        cursor = conn.cursor()

        where = []
        params = []
        if keyword:
            where.append("(i.item_code ILIKE %s OR i.name ILIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category:
            where.append("i.category = %s")
            params.append(category)

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        cursor.execute(
            f"SELECT COUNT(*) FROM items i {where_sql}", params
        )
        total = cursor.fetchone()[0]

        offset = (page - 1) * size
        cursor.execute(
            f"SELECT i.item_code, i.name, i.category, i.unit, i.spec, "
            f"i.safety_stock, COALESCE(SUM(inv.qty), 0) AS stock "
            f"FROM items i "
            f"LEFT JOIN inventory inv ON i.item_code = inv.item_code "
            f"{where_sql} "
            f"GROUP BY i.item_code, i.name, i.category, i.unit, i.spec, "
            f"i.safety_stock "
            f"ORDER BY i.item_code "
            f"LIMIT %s OFFSET %s",
            params + [size, offset],
        )
        rows = cursor.fetchall()
        cursor.close()

        items = [
            {
                "item_code": r[0], "name": r[1], "category": r[2],
                "unit": r[3], "spec": r[4], "safety_stock": r[5],
                "stock": r[6],
            }
            for r in rows
        ]
        return {"items": items, "total": total, "page": page}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_item_detail(item_code: str) -> dict:
    """FN-006: Get item detail."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT item_code, name, category, unit, spec, safety_stock, "
            "created_at FROM items WHERE item_code = %s",
            (item_code,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return {"error": "Item not found."}

        return {
            "item_code": row[0], "name": row[1], "category": row[2],
            "unit": row[3], "spec": row[4], "safety_stock": row[5],
            "created_at": str(row[6]),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def update_item(item_code: str, data: dict) -> dict:
    """FN-007: Update an existing item."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM items WHERE item_code = %s", (item_code,)
        )
        if not cursor.fetchone():
            cursor.close()
            return {"error": "Item not found."}

        sets = []
        params = []
        for field in ("name", "spec", "safety_stock", "category", "unit"):
            if field in data:
                sets.append(f"{field} = %s")
                params.append(data[field])

        if not sets:
            return {"error": "No fields to update."}

        params.append(item_code)
        cursor.execute(
            f"UPDATE items SET {', '.join(sets)} WHERE item_code = %s",
            params,
        )
        conn.commit()
        cursor.close()
        return {"success": True, "updated_at": "now"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
