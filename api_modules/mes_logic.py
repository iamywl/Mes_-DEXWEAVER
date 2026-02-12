"""MES business logic for data retrieval and plan management."""

from psycopg2.extras import RealDictCursor

from .database import get_db, release_conn


def get_full_data():
    """Fetch items and production plans with item names."""
    conn = get_db()
    if not conn:
        return {"items": [], "plans": []}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM items")
            items = cur.fetchall()
            cur.execute(
                "SELECT p.*, i.name as item_name "
                "FROM production_plans p "
                "JOIN items i ON p.item_code = i.item_code "
                "ORDER BY p.due_date DESC"
            )
            return {"items": items, "plans": cur.fetchall()}
    except Exception as e:
        return {"items": [], "plans": [], "error": str(e)}
    finally:
        release_conn(conn)


def add_plan(d):
    """Register a new production plan (REQ-013)."""
    if not d.get("item_code") or d.get("item_code") == "Select Item":
        return {"success": False, "message": "품목을 선택해주세요."}

    conn = get_db()
    if not conn:
        return {"success": False, "message": "데이터베이스 연결에 실패했습니다."}
    try:
        with conn.cursor() as cur:
            sql = (
                "INSERT INTO production_plans "
                "(item_code, plan_qty, due_date, status) "
                "VALUES (%s, %s, %s, 'WAIT')"
            )
            cur.execute(sql, (d["item_code"], d["plan_qty"], d["plan_date"]))
            conn.commit()
            return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        release_conn(conn)
