from .database import query_db

def get_items(): # [REQ-005] 품목조회
    return query_db("SELECT * FROM items ORDER BY item_code")

def get_bom(): # [REQ-008] BOM조회
    return query_db("SELECT * FROM bom")

def get_equipments(): # [REQ-012] 설비현황
    return query_db("SELECT * FROM equipments")
