"""REQ-020: Production dashboard data module.

Provides real-time production status dashboard data including
daily target vs actual quantities and line-level achievement rates.
"""

import logging
from datetime import date

import psycopg2.extras

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def get_production_dashboard_data():
    """
    REQ-020: 실시간 생산 현황 대시보드 데이터를 조회합니다.
    당일 품목별 목표수량 대비 실적수량 및 라인별 달성률을 집계합니다.
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        today = date.today().isoformat()

        query = """
            SELECT
                pp.item_code,
                wo.equip_code,
                SUM(pp.plan_qty) AS target_qty,
                COALESCE(SUM(wr.good_qty), 0) AS actual_qty,
                CASE
                    WHEN SUM(pp.plan_qty) > 0 THEN (COALESCE(SUM(wr.good_qty), 0)::numeric / SUM(pp.plan_qty)) * 100
                    ELSE 0
                END AS achievement_rate
            FROM
                production_plans pp
            JOIN
                work_orders wo ON pp.plan_id = wo.plan_id
            LEFT JOIN
                work_results wr ON wo.wo_id = wr.wo_id
            WHERE
                DATE(wo.work_date) = %s
            GROUP BY
                pp.item_code, wo.equip_code
            ORDER BY
                pp.item_code, wo.equip_code;
        """
        cursor.execute(query, (today,))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        log.error("Database error in get_production_dashboard_data: %s", e)
        return []
    finally:
        if conn:
            release_conn(conn)
