from .database import get_db
from psycopg2.extras import RealDictCursor

def get_full_data(): # 프론트엔드 /api/mes/data 대응
    conn = get_db()
    if not conn: return {"items": [], "plans": []}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM items")
            items = cur.fetchall()
            cur.execute("SELECT p.*, i.name as item_name FROM production_plans p JOIN items i ON p.item_code = i.item_code")
            return {"items": items, "plans": cur.fetchall()}
    finally: conn.close()

def add_plan(d):
    conn = get_db()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO production_plans (item_code, plan_qty, due_date, status) VALUES (%s, %s, %s, 'WAIT')", 
                        (d['item_code'], d['plan_qty'], d['plan_date']))
            conn.commit()
            return True
    finally: conn.close()
