"""REQ-017: Work order creation module.

Creates work orders from production plans with auto-generated IDs
and initial WAIT status.
"""

from datetime import date

import psycopg2.extras

from api_modules.database import get_db, release_conn


async def create_work_order(
    plan_id: str, work_date: date, equip_code: str
):
    """
    REQ-017: 생산 계획 기반으로 작업 지시를 생성합니다.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. production_plans에서 품목 코드와 계획 수량 조회
        plan_query = "SELECT item_code, plan_qty FROM production_plans WHERE plan_id = %s;"
        cursor.execute(plan_query, (plan_id,))
        plan_data = cursor.fetchone()

        if not plan_data:
            raise ValueError(f"Production plan with ID {plan_id} not found.")

        item_code = plan_data['item_code']
        plan_qty = plan_data['plan_qty']

        # 2. 작업지시 ID 생성 (WO-YYYYMMDD-PLAN_ID 형식)
        wo_id = f"WO-{work_date.strftime('%Y%m%d')}-{plan_id}"

        # 3. work_orders 테이블에 작업지시 등록
        insert_wo_query = """
            INSERT INTO work_orders (wo_id, plan_id, item_code, work_date, equip_code, plan_qty, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'WAIT')
            RETURNING wo_id;
        """
        cursor.execute(insert_wo_query, (wo_id, plan_id, item_code, work_date, equip_code, plan_qty))
        created_wo_id = cursor.fetchone()['wo_id']

        conn.commit()
        cursor.close()
        return {"wo_id": created_wo_id, "message": "Work order created successfully."}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
