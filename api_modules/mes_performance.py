from datetime import datetime
from api_modules.database import get_db
import psycopg2.extras

async def register_work_performance_and_update_inventory(
    wo_id: str, good_qty: int, defect_qty: int, worker_id: str, start_time: datetime, end_time: datetime
):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            INSERT INTO work_results (wo_id, good_qty, defect_qty, worker_id, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING result_id;
        """, (wo_id, good_qty, defect_qty, worker_id, start_time, end_time))
        result_id = cursor.fetchone()['result_id']

        cursor.execute("SELECT item_code FROM work_orders WHERE wo_id = %s;", (wo_id,))
        wo_data = cursor.fetchone()
        if not wo_data: raise ValueError(f"Work order {wo_id} not found.")
        item_code = wo_data['item_code']

        cursor.execute("""
            INSERT INTO inventory (item_code, lot_no, qty, warehouse, location)
            VALUES (%s, %s, %s, 'FG_WH', 'FG_LOC')
            ON CONFLICT (item_code, lot_no, warehouse, location) DO UPDATE
            SET qty = inventory.qty + EXCLUDED.qty;
        """, (item_code, wo_id, good_qty))

        cursor.execute("UPDATE work_orders SET status = 'DONE' WHERE wo_id = %s;", (wo_id,))

        conn.commit()
        return {"result_id": result_id, "message": "Work performance registered, inventory updated, and work order completed."}

    except Exception as e:
        if conn: conn.rollback()
        print(f"Error in mes_performance.py: {e}")
        return {"error": str(e)}
    finally:
        if conn: conn.close()
