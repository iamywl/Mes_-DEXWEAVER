"""REQ-074: 복합라우팅 — 재진입/조건분기/병렬/재작업 루프."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_routing(data: dict) -> dict:
    """복합라우팅 생성."""
    routing_code = data.get("routing_code", "").strip()
    item_code = data.get("item_code", "").strip()
    if not routing_code or not item_code:
        return {"error": "routing_code, item_code는 필수입니다."}

    steps = data.get("steps", [])
    if not steps:
        return {"error": "최소 1개 이상의 공정 스텝이 필요합니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        created = []
        for s in steps:
            cursor.execute(
                """INSERT INTO complex_routings
                   (routing_code, item_code, step_order, process_code, step_type,
                    condition_expr, rework_target_step, max_reentry,
                    setup_minutes, cycle_minutes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING routing_id""",
                (routing_code, item_code, s.get("step_order"),
                 s.get("process_code"), s.get("step_type", "SEQUENTIAL"),
                 s.get("condition_expr"), s.get("rework_target_step"),
                 s.get("max_reentry", 1),
                 s.get("setup_minutes", 0), s.get("cycle_minutes", 0)),
            )
            created.append(cursor.fetchone()[0])

        conn.commit()
        cursor.close()
        return {"success": True, "routing_code": routing_code,
                "steps_created": len(created)}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("복합라우팅 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_routing(routing_code: str = None, item_code: str = None) -> dict:
    """복합라우팅 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT routing_id, routing_code, item_code, step_order,
                        process_code, step_type, condition_expr,
                        rework_target_step, max_reentry,
                        setup_minutes, cycle_minutes
                 FROM complex_routings WHERE is_active = TRUE"""
        params = []
        if routing_code:
            sql += " AND routing_code = %s"
            params.append(routing_code)
        if item_code:
            sql += " AND item_code = %s"
            params.append(item_code)
        sql += " ORDER BY routing_code, step_order"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        # 라우팅별 그룹핑
        by_route: dict = {}
        for r in rows:
            rc = r[1]
            if rc not in by_route:
                by_route[rc] = {"routing_code": rc, "item_code": r[2], "steps": []}
            by_route[rc]["steps"].append({
                "step_order": r[3], "process_code": r[4],
                "step_type": r[5], "condition_expr": r[6],
                "rework_target_step": r[7], "max_reentry": r[8],
                "setup_minutes": r[9], "cycle_minutes": r[10],
                "total_minutes": (r[9] or 0) + (r[10] or 0),
            })

        return {"routings": list(by_route.values()), "total": len(by_route)}
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
