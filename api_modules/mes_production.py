from .database import query_db

def add_plan(d): # [REQ-013] 생산계획 등록
    sql = "INSERT INTO production_plans (item_code, plan_qty, due_date, status) VALUES (%s, %s, %s, 'WAIT')"
    return query_db(sql, (d['item_code'], d['plan_qty'], d['due_date']), fetch=False)

def create_work_order(d): # [REQ-017] 작업지시 생성
    sql = "INSERT INTO work_orders (wo_id, plan_id, work_date, equip_code, plan_qty, status) VALUES (%s, %s, %s, %s, %s, 'WAIT')"
    wo_id = f"WO-{d['work_date'].replace('-', '')}-{d['plan_id']}"
    return query_db(sql, (wo_id, d['plan_id'], d['work_date'], d['equip_code'], d['plan_qty']), fetch=False)

def get_work_orders(): # [REQ-018] 작업지시 목록
    return query_db("SELECT * FROM work_orders ORDER BY work_date DESC")
