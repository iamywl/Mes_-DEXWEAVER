"""REQ-068: WO 원가추적 — 노무비/자재비/경비, 표준 vs 실제."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def add_cost(data: dict) -> dict:
    """원가 항목 등록."""
    wo_code = data.get("wo_code", "").strip()
    cost_type = data.get("cost_type", "").strip()

    if not wo_code or not cost_type:
        return {"error": "wo_code, cost_type은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO wo_costs
               (wo_code, cost_type, description, quantity, unit_cost, is_standard)
               VALUES (%s,%s,%s,%s,%s,%s) RETURNING cost_id""",
            (wo_code, cost_type, data.get("description"),
             data.get("quantity", 0), data.get("unit_cost", 0),
             data.get("is_standard", False)),
        )
        cost_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "cost_id": cost_id}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_wo_cost(wo_code: str) -> dict:
    """작업지시별 원가 분석."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT cost_id, cost_type, description, quantity, unit_cost,
                      total_cost, is_standard, created_at
               FROM wo_costs WHERE wo_code = %s ORDER BY cost_type, created_at""",
            (wo_code,),
        )
        rows = cursor.fetchall()
        cursor.close()

        # 유형별 집계
        by_type: dict = {}
        for r in rows:
            ct = r[1]
            if ct not in by_type:
                by_type[ct] = {"standard": 0, "actual": 0, "items": []}
            cost_val = float(r[5]) if r[5] else 0
            if r[6]:
                by_type[ct]["standard"] += cost_val
            else:
                by_type[ct]["actual"] += cost_val
            by_type[ct]["items"].append({
                "cost_id": r[0], "description": r[2],
                "quantity": float(r[3]) if r[3] else 0,
                "unit_cost": float(r[4]) if r[4] else 0,
                "total_cost": cost_val, "is_standard": r[6],
            })

        total_standard = sum(v["standard"] for v in by_type.values())
        total_actual = sum(v["actual"] for v in by_type.values())
        variance = total_actual - total_standard

        return {
            "wo_code": wo_code,
            "by_type": {k: {"standard": round(v["standard"], 2),
                            "actual": round(v["actual"], 2),
                            "variance": round(v["actual"] - v["standard"], 2),
                            "items": v["items"]}
                        for k, v in by_type.items()},
            "total_standard": round(total_standard, 2),
            "total_actual": round(total_actual, 2),
            "total_variance": round(variance, 2),
            "variance_pct": round(variance / total_standard * 100, 1)
                            if total_standard > 0 else 0,
        }
    except Exception as e:
        log.error("원가 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_cost_summary() -> dict:
    """전체 원가 요약."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT wo_code, cost_type,
                      SUM(CASE WHEN is_standard THEN total_cost ELSE 0 END) AS std,
                      SUM(CASE WHEN NOT is_standard THEN total_cost ELSE 0 END) AS act
               FROM wo_costs
               GROUP BY wo_code, cost_type
               ORDER BY wo_code, cost_type""",
        )
        rows = cursor.fetchall()
        cursor.close()

        by_wo: dict = {}
        for r in rows:
            wo = r[0]
            if wo not in by_wo:
                by_wo[wo] = {"wo_code": wo, "standard": 0, "actual": 0, "types": {}}
            s = float(r[2]) if r[2] else 0
            a = float(r[3]) if r[3] else 0
            by_wo[wo]["standard"] += s
            by_wo[wo]["actual"] += a
            by_wo[wo]["types"][r[1]] = {"standard": round(s, 2), "actual": round(a, 2)}

        for wo in by_wo.values():
            wo["standard"] = round(wo["standard"], 2)
            wo["actual"] = round(wo["actual"], 2)
            wo["variance"] = round(wo["actual"] - wo["standard"], 2)

        return {"items": list(by_wo.values()), "total_wo": len(by_wo)}
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
