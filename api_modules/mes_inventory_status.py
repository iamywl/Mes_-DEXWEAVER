from api_modules.database import get_db, release_conn
import psycopg2.extras

async def get_inventory_status(item_code: str = None):
    """
    REQ-026: 실시간 재고 현황을 조회합니다.
    품목코드, 로트번호, 창고, 위치, 현재고를 반환합니다.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            SELECT
                item_code, lot_no, qty, warehouse, location
            FROM
                inventory
        """
        params = []

        if item_code:
            query += " WHERE item_code = %s"
            params.append(item_code)
        
        query += " ORDER BY item_code, lot_no;"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        release_conn(conn)
        return results
    except Exception as e:
        print(f"Database error in get_inventory_status: {e}")
        if conn:
            release_conn(conn)
        return []
