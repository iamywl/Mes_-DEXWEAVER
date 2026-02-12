from .database import query_db

def register_incoming(d): # [REQ-025] 입고등록
    sql = "INSERT INTO inventory (item_code, lot_no, qty, warehouse, location) VALUES (%s, %s, %s, %s, %s)"
    return query_db(sql, (d['item_code'], d['lot_no'], d['qty'], d['warehouse'], d['location']), fetch=False)

def register_outgoing(d): # [REQ-026] 출고등록 (단순화)
    sql = "UPDATE inventory SET qty = qty - %s WHERE item_code = %s AND lot_no = %s"
    return query_db(sql, (d['qty'], d['item_code'], d['lot_no']), fetch=False)

def get_inventory(): # [REQ-027] 재고현황
    return query_db("SELECT item_code, SUM(qty) as stock FROM inventory GROUP BY item_code")
