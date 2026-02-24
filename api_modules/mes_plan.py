"""FN-015~019: Production plan management module."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

try:
    from ortools.sat.python import cp_model
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False
    log.warning("OR-Tools not installed – falling back to greedy heuristic.")


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
    """FN-019: AI schedule optimization using OR-Tools CP-SAT solver."""
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

        # Calculate durations
        jobs = []
        for p in plans:
            plan_id, item_code, qty, due_date, priority = p
            durations = []
            for e in equips:
                cap = e[2] if e[2] > 0 else 1
                dur = max(1, int(qty / (cap / 60)))
                durations.append((e[0], dur))
            priority_weight = {"HIGH": 3, "MID": 2, "LOW": 1}.get(priority, 2)
            jobs.append({
                "plan_id": plan_id, "item_code": item_code,
                "qty": qty, "due_date": due_date,
                "priority_weight": priority_weight,
                "durations": durations,
            })

        if HAS_ORTOOLS:
            result = _ortools_schedule(jobs, equips)
        else:
            result = _greedy_schedule(jobs, equips)

        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


def _ortools_schedule(jobs, equips):
    """OR-Tools CP-SAT constraint programming solver."""
    model = cp_model.CpModel()

    # Upper bound for makespan
    max_duration = sum(max(d for _, d in j["durations"]) for j in jobs)

    # Decision variables
    job_vars = []
    for i, job in enumerate(jobs):
        start = model.new_int_var(0, max_duration, f"start_{i}")
        end = model.new_int_var(0, max_duration, f"end_{i}")

        # Machine assignment (one machine per job)
        machine_bools = []
        for m, (equip_code, dur) in enumerate(job["durations"]):
            b = model.new_bool_var(f"job{i}_m{m}")
            machine_bools.append((b, dur, equip_code, m))

        # Exactly one machine per job
        model.add_exactly_one(b for b, _, _, _ in machine_bools)

        # Link duration to machine choice
        for b, dur, _, _ in machine_bools:
            model.add(end == start + dur).only_enforce_if(b)

        job_vars.append({
            "start": start, "end": end,
            "machine_bools": machine_bools, "job": job,
        })

    # No overlap on same machine: for each pair of jobs on same machine
    for i in range(len(job_vars)):
        for j in range(i + 1, len(job_vars)):
            for mi, (bi, di, ei, idx_i) in enumerate(job_vars[i]["machine_bools"]):
                for mj, (bj, dj, ej, idx_j) in enumerate(job_vars[j]["machine_bools"]):
                    if ei == ej:  # same machine
                        # Either i before j, or j before i (when both assigned here)
                        both = model.new_bool_var(f"both_{i}_{j}_{ei}")
                        model.add_implication(both, bi)
                        model.add_implication(both, bj)
                        model.add_implication(bi.negated(), both.negated())
                        model.add_implication(bj.negated(), both.negated())

                        order = model.new_bool_var(f"order_{i}_{j}_{ei}")
                        model.add(
                            job_vars[i]["end"] <= job_vars[j]["start"]
                        ).only_enforce_if(both, order)
                        model.add(
                            job_vars[j]["end"] <= job_vars[i]["start"]
                        ).only_enforce_if(both, order.negated())

    # Objective: minimize weighted makespan + priority penalties
    makespan = model.new_int_var(0, max_duration, "makespan")
    for jv in job_vars:
        model.add(makespan >= jv["end"])

    # Priority: high-priority jobs should finish earlier
    priority_cost = []
    for jv in job_vars:
        w = jv["job"]["priority_weight"]
        priority_cost.append(jv["end"] * w)

    model.minimize(makespan * 10 + sum(priority_cost))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for seq, jv in enumerate(job_vars, 1):
            start_val = solver.value(jv["start"])
            end_val = solver.value(jv["end"])
            assigned_equip = None
            for b, dur, ec, _ in jv["machine_bools"]:
                if solver.value(b):
                    assigned_equip = ec
                    break
            schedule.append({
                "plan_id": jv["job"]["plan_id"],
                "equip": assigned_equip,
                "start_min": start_val,
                "end_min": end_val,
                "duration_min": end_val - start_val,
                "seq": seq,
            })

        ms = solver.value(makespan)
        total_work = sum(s["duration_min"] for s in schedule)
        util = round(total_work / (ms * len(equips)), 2) if ms > 0 else 0

        return {
            "solver": "OR-Tools CP-SAT",
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
            "schedule": schedule,
            "makespan": ms,
            "utilization": util,
        }
    else:
        # Fallback to greedy if solver fails
        return _greedy_schedule(
            [jv["job"] for jv in job_vars], equips
        )


def _greedy_schedule(jobs, equips):
    """Greedy heuristic fallback scheduler."""
    schedule = []
    equip_time = {e[0]: 0 for e in equips}
    seq = 0

    for job in jobs:
        best_equip = min(equip_time, key=equip_time.get)
        dur = next(d for ec, d in job["durations"] if ec == best_equip)

        start_min = equip_time[best_equip]
        end_min = start_min + dur
        equip_time[best_equip] = end_min

        seq += 1
        schedule.append({
            "plan_id": job["plan_id"],
            "equip": best_equip,
            "start_min": start_min,
            "end_min": end_min,
            "duration_min": dur,
            "seq": seq,
        })

    makespan = max(equip_time.values()) if equip_time else 0
    total_work = sum(equip_time.values())
    utilization = round(
        total_work / (makespan * len(equips)), 2
    ) if makespan > 0 else 0

    return {
        "solver": "Greedy",
        "status": "HEURISTIC",
        "schedule": schedule,
        "makespan": makespan,
        "utilization": utilization,
    }
