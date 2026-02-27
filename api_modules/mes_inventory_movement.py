"""REQ-028: Inventory movement module.

Provides warehouse-to-warehouse inventory transfer functionality
within a single transaction for data integrity.
"""

import psycopg2.extras

from api_modules.database import get_db, release_conn


async def move_inventory(
    item_code: str, lot_no: str, qty: int, from_location: str, to_location: str
):
    """
    REQ-028: 창고 간 재고 이동 기능을 구현합니다.
    단일 트랜잭션으로 출발지에서 수량을 차감하고 목적지에 가산합니다.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. 출발지 재고 차감
        update_from_query = """
            UPDATE inventory
            SET qty = qty - %s
            WHERE item_code = %s AND lot_no = %s AND location = %s
            RETURNING qty;
        """
        cursor.execute(update_from_query, (qty, item_code, lot_no, from_location))
        if not cursor.fetchone():
            raise ValueError("Insufficient stock or invalid source location.")

        # 2. 목적지 재고 가산 또는 신규 생성
        insert_or_update_to_query = """
            INSERT INTO inventory (item_code, lot_no, qty, warehouse, location)
            VALUES (%s, %s, %s, (SELECT warehouse FROM inventory WHERE item_code = %s AND lot_no = %s LIMIT 1), %s)
            ON CONFLICT (item_code, lot_no, location) DO UPDATE
            SET qty = inventory.qty + EXCLUDED.qty;
        """
        cursor.execute(insert_or_update_to_query, (item_code, lot_no, qty, item_code, lot_no, to_location))

        conn.commit()
        cursor.close()
        return {"message": f"Inventory of {item_code} (Lot: {lot_no}) moved from {from_location} to {to_location}."}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
