"""REQ-025: Material receipt module.

Processes material receiving with auto-generated lot numbers
and registers inventory records.
"""

import uuid
from datetime import datetime

import psycopg2.extras

from api_modules.database import get_db, release_conn


async def register_material_receipt(
    item_code: str, qty: int, warehouse: str, location: str
):
    """
    REQ-025: 자재 입고를 처리하고 로트 번호를 생성하여 재고에 등록합니다.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 로트 번호 생성: MAT-LOT-YYYYMMDD-UUID_SHORT
        today_str = datetime.now().strftime('%Y%m%d')
        lot_suffix = str(uuid.uuid4())[:8]
        lot_no = f"MAT-LOT-{today_str}-{lot_suffix}"

        insert_query = """
            INSERT INTO inventory (item_code, lot_no, qty, warehouse, location)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING lot_no, item_code, qty;
        """
        cursor.execute(insert_query, (item_code, lot_no, qty, warehouse, location))
        result = cursor.fetchone()

        conn.commit()
        cursor.close()
        return {"lot_no": result['lot_no'], "message": "Material receipt registered successfully."}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
