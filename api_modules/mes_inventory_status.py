"""REQ-026: Real-time inventory status module.

Provides inventory status queries including item code,
lot number, warehouse, location and current stock quantities.
"""

import logging

import psycopg2.extras

from api_modules.database import db_connection

log = logging.getLogger(__name__)


async def get_inventory_status(item_code: str = None):
    """
    REQ-026: 실시간 재고 현황을 조회합니다.
    품목코드, 로트번호, 창고, 위치, 현재고를 반환합니다.
    """
    try:
        with db_connection() as conn:
            if not conn:
                return []
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
            return results
    except Exception as e:
        log.error("Database error in get_inventory_status: %s", e)
        return []
