"""REQ-040: CMMS 유지보전 — PM 일정, 정비 작업지시, 정비 이력/KPI (FN-049~051)."""

import logging
from datetime import datetime, timedelta

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


# ── FN-049: PM 일정 등록 ────────────────────────────────────

async def create_pm_schedule(data: dict) -> dict:
    """PM 일정 등록."""
    equip_code = data.get("equip_code", "").strip()
    if not equip_code:
        return {"error": "equip_code는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        interval_days = data.get("interval_days", 30)
        next_due = data.get("start_date") or (
            datetime.now() + timedelta(days=interval_days)).strftime("%Y-%m-%d")

        cursor.execute(
            """INSERT INTO maintenance_plans
               (equip_code, pm_type, interval_days, interval_hours, checklist,
                next_due, status, assignee, description)
               VALUES (%s, %s, %s, %s, %s::jsonb, %s, 'ACTIVE', %s, %s)
               RETURNING pm_id""",
            (equip_code, data.get("pm_type", "TIME_BASED"),
             interval_days, data.get("interval_hours"),
             __import__("json").dumps(data.get("checklist", [])),
             next_due, data.get("assignee"), data.get("description", "")),
        )
        pm_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "pm_id": pm_id, "next_due": next_due}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("PM 일정 등록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_pm_schedules(equip_code: str = None, status: str = None) -> dict:
    """PM 일정 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT pm_id, equip_code, pm_type, interval_days, interval_hours,
                        checklist, next_due, status, assignee, description, created_at
                 FROM maintenance_plans WHERE 1=1"""
        params = []
        if equip_code:
            sql += " AND equip_code = %s"
            params.append(equip_code)
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY next_due ASC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "pm_id": r[0], "equip_code": r[1], "pm_type": r[2],
                    "interval_days": r[3], "interval_hours": r[4],
                    "checklist": r[5] or [], "next_due": r[6].isoformat() if r[6] else None,
                    "status": r[7], "assignee": r[8], "description": r[9],
                    "created_at": r[10].isoformat() if r[10] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


# ── FN-050: 정비 작업지시 ───────────────────────────────────

async def create_maintenance_order(data: dict) -> dict:
    """정비 작업지시 생성."""
    equip_code = data.get("equip_code", "").strip()
    if not equip_code:
        return {"error": "equip_code는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT COUNT(*) FROM maintenance_orders WHERE mo_id LIKE %s",
            (f"MWO-{today}-%",),
        )
        seq = (cursor.fetchone()[0] or 0) + 1
        mo_id = f"MWO-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO maintenance_orders
               (mo_id, equip_code, mo_type, source, pm_id, description,
                priority, status, assigned_to)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'PLANNED', %s)""",
            (mo_id, equip_code,
             data.get("mo_type", "PM"), data.get("source", "MANUAL"),
             data.get("pm_id"), data.get("description", ""),
             data.get("priority", "NORMAL"), data.get("assigned_to")),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "mo_id": mo_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("정비 작업지시 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def update_maintenance_order(mo_id: str, data: dict) -> dict:
    """정비 작업지시 상태 변경."""
    new_status = data.get("status", "").strip()
    if not new_status:
        return {"error": "status는 필수입니다."}

    valid_transitions = {
        "PLANNED": ["IN_PROGRESS", "CANCELLED"],
        "IN_PROGRESS": ["COMPLETED", "CANCELLED"],
    }

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM maintenance_orders WHERE mo_id = %s", (mo_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": f"정비 작업지시 '{mo_id}'를 찾을 수 없습니다."}

        current = row[0]
        allowed = valid_transitions.get(current, [])
        if new_status not in allowed:
            cursor.close()
            return {"error": f"'{current}' → '{new_status}' 전이 불가. 가능: {allowed}"}

        updates = ["status = %s"]
        params = [new_status]

        if new_status == "IN_PROGRESS":
            updates.append("start_time = NOW()")
        elif new_status == "COMPLETED":
            updates.append("end_time = NOW()")
            if data.get("cost"):
                updates.append("cost = %s")
                params.append(data["cost"])
            if data.get("parts_used"):
                updates.append("parts_used = %s::jsonb")
                params.append(__import__("json").dumps(data["parts_used"]))
            # 소요시간 자동 계산
            updates.append(
                "duration_min = EXTRACT(EPOCH FROM NOW() - start_time)::int / 60")

        params.append(mo_id)
        cursor.execute(
            f"UPDATE maintenance_orders SET {', '.join(updates)} WHERE mo_id = %s",
            tuple(params),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "mo_id": mo_id, "status": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("정비 작업지시 변경 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


# ── FN-051: 정비 이력 조회 / KPI ────────────────────────────

async def get_maintenance_history(equip_code: str,
                                   mo_type: str = None,
                                   start_date: str = None,
                                   end_date: str = None) -> dict:
    """정비 이력 + KPI(MTBF/MTTR/Availability)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT mo_id, equip_code, mo_type, source, description, priority,
                        status, assigned_to, start_time, end_time,
                        duration_min, cost, parts_used, created_at
                 FROM maintenance_orders WHERE equip_code = %s"""
        params = [equip_code]
        if mo_type:
            sql += " AND mo_type = %s"
            params.append(mo_type)
        if start_date:
            sql += " AND created_at >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND created_at <= %s"
            params.append(end_date)
        sql += " ORDER BY created_at DESC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        history = [
            {
                "mo_id": r[0], "equip_code": r[1], "mo_type": r[2],
                "source": r[3], "description": r[4], "priority": r[5],
                "status": r[6], "assigned_to": r[7],
                "start_time": r[8].isoformat() if r[8] else None,
                "end_time": r[9].isoformat() if r[9] else None,
                "duration_min": r[10], "cost": float(r[11]) if r[11] else 0,
                "parts_used": r[12] or [],
                "created_at": r[13].isoformat() if r[13] else None,
            }
            for r in rows
        ]

        # KPI 계산
        completed = [h for h in history if h["status"] == "COMPLETED"]
        cm_count = sum(1 for h in completed if h["mo_type"] in ("CM", "BM"))
        total_repair = sum(h["duration_min"] or 0 for h in completed
                          if h["mo_type"] in ("CM", "BM"))
        total_cost = sum(h["cost"] for h in completed)
        pm_scheduled = sum(1 for h in history if h["mo_type"] == "PM")
        pm_done = sum(1 for h in completed if h["mo_type"] == "PM")

        mttr = (total_repair / cm_count / 60) if cm_count > 0 else 0
        availability = 1.0 - (total_repair / (30 * 24 * 60)) if total_repair else 1.0

        return {
            "equip_code": equip_code,
            "history": history,
            "statistics": {
                "total_orders": len(history),
                "completed": len(completed),
                "cm_count": cm_count,
                "pm_compliance": round(pm_done / pm_scheduled * 100, 1) if pm_scheduled else 0,
                "mttr_hours": round(mttr, 2),
                "availability": round(max(0, availability) * 100, 1),
                "total_cost": total_cost,
            },
        }
    except Exception as e:
        log.error("정비 이력 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
