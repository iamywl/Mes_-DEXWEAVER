from .database import get_db
from psycopg2.extras import RealDictCursor

def get_mes_data():
    conn = get_db()
    if not conn: return {"items": [], "plans": []}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM items"); items = cur.fetchall()
            cur.execute("SELECT p.*, i.name as item_name FROM production_plans p JOIN items i ON p.item_code = i.item_code ORDER BY p.plan_date DESC")
            return {"items": items, "plans": cur.fetchall()}
    except: return {"items": [], "plans": []}
    finally: conn.close()
