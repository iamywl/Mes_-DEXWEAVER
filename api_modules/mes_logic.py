from .database import get_db
from psycopg2.extras import RealDictCursor

def get_full_data():
    conn = get_db()
    if not conn: return {"items": [], "plans": []}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM items")
            items = cur.fetchall()
            cur.execute("SELECT p.*, i.name as item_name FROM production_plans p JOIN items i ON p.item_code = i.item_code ORDER BY p.due_date DESC")
            return {"items": items, "plans": cur.fetchall()}
    except Exception as e: return {"items": [], "plans": [], "error": str(e)}
    finally: conn.close()

def add_plan(d):
    # 500 에러 방지를 위한 필수 값 검증
    if not d.get('item_code') or d.get('item_code') == 'Select Item':
        return {"success": False, "message": "품목을 선택해주세요."}
    
    conn = get_db()
    if not conn: return {"success": False, "message": "데이터베이스 연결에 실패했습니다."}
    try:
        with conn.cursor() as cur:
            # 프론트엔드의 plan_date를 DB의 due_date 컬럼에 매핑 [REQ-013]
            sql = "INSERT INTO production_plans (item_code, plan_qty, due_date, status) VALUES (%s, %s, %s, 'WAIT')"
            cur.execute(sql, (d['item_code'], d['plan_qty'], d['plan_date']))
            conn.commit()
            return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally: conn.close()
