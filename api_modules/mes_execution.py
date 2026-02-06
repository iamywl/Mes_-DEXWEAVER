from .db_core import query_db

def register_result(d): # [REQ-019] 작업실적 등록
    sql = """INSERT INTO work_results (wo_id, good_qty, defect_qty, worker_id, start_time, end_time) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    res = query_db(sql, (d['wo_id'], d['good_qty'], d['defect_qty'], d['worker_id'], d['start_time'], d['end_time']), fetch=False)
    # 실적 등록 시 작업지시 상태를 DONE으로 변경
    query_db("UPDATE work_orders SET status = 'DONE' WHERE wo_id = %s", (d['wo_id'],), fetch=False)
    return res

def get_production_dashboard(): # [REQ-020] 생산현황 대시보드
    sql = "SELECT wo_id, SUM(good_qty) as total_good FROM work_results GROUP BY wo_id"
    return query_db(sql)
