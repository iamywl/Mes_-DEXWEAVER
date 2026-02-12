"""FN-020~024: Work order and production execution module."""

from datetime import date

from api_modules.database import get_conn, release_conn


async def create_work_order(data: dict) -> dict:
    """FN-020: Create a work order from a plan."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        plan_id = data["plan_id"]

        # Get plan info
        cursor.execute(
            "SELECT item_code, plan_qty FROM production_plans "
            "WHERE plan_id = %s",
            (plan_id,),
        )
        plan = cursor.fetchone()
        if not plan:
            cursor.close()
            return {"error": "Plan not found."}

        work_date = data.get("work_date", str(date.today()))

        # Generate WO ID: WO-YYYYMMDD-SEQ
        date_part = work_date.replace("-", "")
        cursor.execute(
            "SELECT COUNT(*) FROM work_orders "
            "WHERE wo_id LIKE %s",
            (f"WO-{date_part}-%",),
        )
        seq = cursor.fetchone()[0] + 1
        wo_id = f"WO-{date_part}-{seq:03d}"

        cursor.execute(
            "INSERT INTO work_orders "
            "(wo_id, plan_id, item_code, work_date, equip_code, plan_qty, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, 'WAIT')",
            (wo_id, plan_id, plan[0], work_date,
             data.get("equip_code"), data.get("plan_qty", plan[1])),
        )

        # Update plan status to PROGRESS
        cursor.execute(
            "UPDATE production_plans SET status = 'PROGRESS' "
            "WHERE plan_id = %s AND status = 'WAIT'",
            (plan_id,),
        )

        conn.commit()
        cursor.close()
        return {"work_order_id": wo_id, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_work_orders(work_date: str = None, line_id: str = None,
                          status: str = None) -> dict:
    """FN-021: List work orders with filters."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"orders": []}

        cursor = conn.cursor()

        where = []
        params = []
        if work_date:
            where.append("wo.work_date = %s")
            params.append(work_date)
        if status:
            where.append("wo.status = %s")
            params.append(status)

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        cursor.execute(
            f"SELECT wo.wo_id, i.name, wo.plan_qty, wo.status, "
            f"wo.work_date, wo.equip_code "
            f"FROM work_orders wo "
            f"JOIN items i ON wo.item_code = i.item_code "
            f"{where_sql} "
            f"ORDER BY wo.work_date DESC, wo.wo_id",
            params,
        )
        rows = cursor.fetchall()
        cursor.close()

        orders = [
            {
                "wo_id": r[0], "item_name": r[1], "plan_qty": r[2],
                "status": r[3], "work_date": str(r[4]),
                "equip_code": r[5],
            }
            for r in rows
        ]
        return {"orders": orders}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_work_order_detail(wo_id: str) -> dict:
    """FN-022: Get work order detail."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT wo.wo_id, i.item_code, i.name, wo.plan_qty, "
            "wo.status, wo.work_date, wo.equip_code "
            "FROM work_orders wo "
            "JOIN items i ON wo.item_code = i.item_code "
            "WHERE wo.wo_id = %s",
            (wo_id,),
        )
        wo = cursor.fetchone()
        if not wo:
            cursor.close()
            return {"error": "Work order not found."}

        # Get results
        cursor.execute(
            "SELECT result_id, good_qty, defect_qty, worker_id, "
            "start_time, end_time "
            "FROM work_results WHERE wo_id = %s",
            (wo_id,),
        )
        results = cursor.fetchall()

        # Get routing
        cursor.execute(
            "SELECT r.seq, p.name, r.cycle_time "
            "FROM routings r "
            "JOIN processes p ON r.process_code = p.process_code "
            "WHERE r.item_code = %s ORDER BY r.seq",
            (wo[1],),
        )
        routing = cursor.fetchall()
        cursor.close()

        total_good = sum(r[1] for r in results)
        progress = round(total_good / wo[3] * 100, 1) if wo[3] > 0 else 0

        return {
            "wo_id": wo[0],
            "item": {"code": wo[1], "name": wo[2]},
            "qty": wo[3],
            "status": wo[4],
            "work_date": str(wo[5]),
            "equip_code": wo[6],
            "progress_pct": progress,
            "routing": [
                {"seq": r[0], "process": r[1], "cycle_time": r[2]}
                for r in routing
            ],
            "results": [
                {
                    "result_id": r[0], "good_qty": r[1],
                    "defect_qty": r[2], "worker_id": r[3],
                    "start_time": str(r[4]) if r[4] else None,
                    "end_time": str(r[5]) if r[5] else None,
                }
                for r in results
            ],
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def create_work_result(data: dict) -> dict:
    """FN-023: Register work result."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        wo_id = data["wo_id"]

        cursor.execute(
            "INSERT INTO work_results "
            "(wo_id, good_qty, defect_qty, defect_code, worker_id, "
            "start_time, end_time) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING result_id",
            (
                wo_id,
                data.get("good_qty", 0),
                data.get("defect_qty", 0),
                data.get("defect_code"),
                data.get("worker_id"),
                data.get("start_time"),
                data.get("end_time"),
            ),
        )
        result_id = cursor.fetchone()[0]

        # Calculate progress and update work order status
        cursor.execute(
            "SELECT wo.plan_qty, COALESCE(SUM(wr.good_qty), 0) "
            "FROM work_orders wo "
            "LEFT JOIN work_results wr ON wo.wo_id = wr.wo_id "
            "WHERE wo.wo_id = %s GROUP BY wo.plan_qty",
            (wo_id,),
        )
        row = cursor.fetchone()
        progress = 0
        if row:
            progress = round(row[1] / row[0] * 100, 1) if row[0] > 0 else 0
            if row[1] >= row[0]:
                cursor.execute(
                    "UPDATE work_orders SET status = 'DONE' "
                    "WHERE wo_id = %s",
                    (wo_id,),
                )

        # Update work order to WORKING if still WAIT
        cursor.execute(
            "UPDATE work_orders SET status = 'WORKING' "
            "WHERE wo_id = %s AND status = 'WAIT'",
            (wo_id,),
        )

        conn.commit()
        cursor.close()
        return {
            "result_id": result_id,
            "progress_pct": progress,
            "success": True,
        }
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_dashboard(target_date: str = None) -> dict:
    """FN-024: Production dashboard data."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"lines": [], "hourly": []}

        if not target_date:
            target_date = str(date.today())

        cursor = conn.cursor()

        # Line-level summary
        cursor.execute(
            "SELECT wo.equip_code, "
            "SUM(wo.plan_qty) AS target, "
            "COALESCE(SUM(wr.good_qty), 0) AS actual, "
            "MAX(wo.status) AS status "
            "FROM work_orders wo "
            "LEFT JOIN work_results wr ON wo.wo_id = wr.wo_id "
            "WHERE wo.work_date = %s "
            "GROUP BY wo.equip_code",
            (target_date,),
        )
        lines = cursor.fetchall()

        # Hourly breakdown
        cursor.execute(
            "SELECT EXTRACT(HOUR FROM wr.start_time)::int AS hour, "
            "SUM(wr.good_qty) AS qty "
            "FROM work_results wr "
            "JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            "WHERE wo.work_date = %s AND wr.start_time IS NOT NULL "
            "GROUP BY EXTRACT(HOUR FROM wr.start_time) "
            "ORDER BY hour",
            (target_date,),
        )
        hourly = cursor.fetchall()
        cursor.close()

        return {
            "date": target_date,
            "lines": [
                {
                    "line_id": r[0] or "UNASSIGNED",
                    "target": r[1], "actual": r[2],
                    "rate": round(r[2] / r[1], 2) if r[1] > 0 else 0,
                    "status": r[3],
                }
                for r in lines
            ],
            "hourly": [
                {"hour": r[0], "qty": r[1]}
                for r in hourly
            ],
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
