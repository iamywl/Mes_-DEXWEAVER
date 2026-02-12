"""FN-015~019: Production plan management module."""

from api_modules.database import get_conn, release_conn


async def create_plan(data: dict) -> dict:
    """FN-015: Create a production plan."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO production_plans "
            "(item_code, plan_qty, due_date, priority, status) "
            "VALUES (%s, %s, %s, %s, 'WAIT') RETURNING plan_id",
            (
                data["item_code"],
                data["plan_qty"],
                data["due_date"],
                data.get("priority", "MID"),
            ),
        )
        plan_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"plan_id": plan_id, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_plans(start_date: str = None, end_date: str = None,
                    status: str = None, page: int = 1) -> dict:
    """FN-016: List production plans with filters."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"plans": [], "total": 0}

        cursor = conn.cursor()

        where = []
        params = []
        if start_date:
            where.append("p.due_date >= %s")
            params.append(start_date)
        if end_date:
            where.append("p.due_date <= %s")
            params.append(end_date)
        if status:
            where.append("p.status = %s")
            params.append(status)

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        cursor.execute(
            f"SELECT COUNT(*) FROM production_plans p {where_sql}", params
        )
        total = cursor.fetchone()[0]

        offset = (page - 1) * 20
        cursor.execute(
            f"SELECT p.plan_id, i.name, p.plan_qty, p.due_date, "
            f"p.status, p.priority, "
            f"COALESCE(SUM(wr.good_qty), 0) AS done_qty "
            f"FROM production_plans p "
            f"JOIN items i ON p.item_code = i.item_code "
            f"LEFT JOIN work_orders wo ON p.plan_id = wo.plan_id "
            f"LEFT JOIN work_results wr ON wo.wo_id = wr.wo_id "
            f"{where_sql} "
            f"GROUP BY p.plan_id, i.name, p.plan_qty, p.due_date, "
            f"p.status, p.priority "
            f"ORDER BY p.due_date "
            f"LIMIT 20 OFFSET %s",
            params + [offset],
        )
        rows = cursor.fetchall()
        cursor.close()

        plans = []
        for r in rows:
            progress = round(r[6] / r[2] * 100, 1) if r[2] > 0 else 0
            plans.append({
                "plan_id": r[0], "item_name": r[1], "qty": r[2],
                "due_date": str(r[3]), "status": r[4],
                "priority": r[5], "progress": progress,
            })
        return {"plans": plans, "total": total}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_plan_detail(plan_id: int) -> dict:
    """FN-017: Get plan detail with linked work orders."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.plan_id, i.item_code, i.name, p.plan_qty, "
            "p.due_date, p.status, p.priority "
            "FROM production_plans p "
            "JOIN items i ON p.item_code = i.item_code "
            "WHERE p.plan_id = %s",
            (plan_id,),
        )
        plan = cursor.fetchone()
        if not plan:
            cursor.close()
            return {"error": "Plan not found."}

        cursor.execute(
            "SELECT wo.wo_id, wo.work_date, wo.plan_qty, wo.status, "
            "COALESCE(SUM(wr.good_qty), 0) AS done "
            "FROM work_orders wo "
            "LEFT JOIN work_results wr ON wo.wo_id = wr.wo_id "
            "WHERE wo.plan_id = %s "
            "GROUP BY wo.wo_id, wo.work_date, wo.plan_qty, wo.status",
            (plan_id,),
        )
        orders = cursor.fetchall()
        cursor.close()

        total_done = sum(o[4] for o in orders)
        progress = round(total_done / plan[3] * 100, 1) if plan[3] > 0 else 0

        return {
            "plan_id": plan[0],
            "item": {"code": plan[1], "name": plan[2]},
            "qty": plan[3],
            "due_date": str(plan[4]),
            "status": plan[5],
            "priority": plan[6],
            "progress_pct": progress,
            "work_orders": [
                {
                    "wo_id": o[0], "work_date": str(o[1]),
                    "qty": o[2], "status": o[3], "done_qty": o[4],
                }
                for o in orders
            ],
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def schedule_optimize(data: dict) -> dict:
    """FN-019: AI schedule optimization (greedy heuristic)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        plan_ids = data.get("plan_ids", [])

        if not plan_ids:
            return {"error": "No plan_ids provided."}

        placeholders = ",".join(["%s"] * len(plan_ids))
        cursor.execute(
            f"SELECT p.plan_id, p.item_code, p.plan_qty, p.due_date, "
            f"p.priority "
            f"FROM production_plans p "
            f"WHERE p.plan_id IN ({placeholders}) "
            f"ORDER BY p.due_date, "
            f"CASE p.priority WHEN 'HIGH' THEN 1 "
            f"WHEN 'MID' THEN 2 ELSE 3 END",
            plan_ids,
        )
        plans = cursor.fetchall()

        cursor.execute(
            "SELECT equip_code, name, capacity_per_hour "
            "FROM equipments WHERE status != 'DOWN' "
            "ORDER BY capacity_per_hour DESC"
        )
        equips = cursor.fetchall()
        cursor.close()

        if not equips:
            return {"error": "No available equipment."}

        # Simple greedy scheduling
        schedule = []
        equip_time = {e[0]: 0 for e in equips}
        seq = 0

        for p in plans:
            plan_id, item_code, qty, due_date, priority = p
            # Pick equipment with least load
            best_equip = min(equip_time, key=equip_time.get)
            cap = next(e[2] for e in equips if e[0] == best_equip)
            duration_min = int(qty / max(cap / 60, 1))

            start_min = equip_time[best_equip]
            end_min = start_min + duration_min
            equip_time[best_equip] = end_min

            seq += 1
            schedule.append({
                "plan_id": plan_id,
                "equip": best_equip,
                "start_min": start_min,
                "end_min": end_min,
                "duration_min": duration_min,
                "seq": seq,
            })

        makespan = max(equip_time.values()) if equip_time else 0
        total_cap = sum(equip_time.values())
        utilization = round(
            total_cap / (makespan * len(equips)), 2
        ) if makespan > 0 else 0

        return {
            "schedule": schedule,
            "makespan": makespan,
            "utilization": utilization,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
