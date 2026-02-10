from datetime import datetime
from api_modules.database import get_db

async def register_work_performance(
    wo_id: str,
    good_qty: int,
    defect_qty: int,
    worker_id: str,
    start_time: datetime,
    end_time: datetime
):
    """
    REQ-019: 작업 실적을 등록하고 작업 지시의 상태를 업데이트합니다.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 1. 작업 실적 등록
        insert_query = """
            INSERT INTO work_results (wo_id, good_qty, defect_qty, worker_id, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING result_id;
        """
        cursor.execute(insert_query, (wo_id, good_qty, defect_qty, worker_id, start_time, end_time))
        result_id = cursor.fetchone()[0]

        # 2. 작업 지시 상태 업데이트 (DONE으로 변경)
        update_wo_query = """
            UPDATE work_orders
            SET status = 'DONE'
            WHERE wo_id = %s;
        """
        cursor.execute(update_wo_query, (wo_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return {"result_id": result_id, "message": "Work performance registered and work order updated successfully."}

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return {"error": str(e)}