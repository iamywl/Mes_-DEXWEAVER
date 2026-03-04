"""REQ-050: 통합 리소스 관리 — 설비/작업자/금형/치공구/게이지 (FN-066)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def get_resources(resource_type: str = None, status: str = None,
                        keyword: str = None) -> dict:
    """FN-066: 통합 리소스 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT resource_id, resource_code, resource_type, name,
                        status, location, capacity, unit,
                        current_usage, last_maintenance, is_active, created_at
                 FROM resources WHERE is_active = TRUE"""
        params = []
        if resource_type:
            sql += " AND resource_type = %s"
            params.append(resource_type)
        if status:
            sql += " AND status = %s"
            params.append(status)
        if keyword:
            sql += " AND (name ILIKE %s OR resource_code ILIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        sql += " ORDER BY resource_type, resource_code LIMIT 500"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        return {
            "items": [
                {
                    "resource_id": r[0], "resource_code": r[1],
                    "resource_type": r[2], "name": r[3], "status": r[4],
                    "location": r[5], "capacity": float(r[6]) if r[6] else None,
                    "unit": r[7], "current_usage": float(r[8]) if r[8] else 0,
                    "utilization": round(float(r[8]) / float(r[6]) * 100, 1)
                        if r[6] and r[8] and float(r[6]) > 0 else 0,
                    "last_maintenance": r[9].isoformat() if r[9] else None,
                    "created_at": r[11].isoformat() if r[11] else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }
    except Exception as e:
        log.error("리소스 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def create_resource(data: dict) -> dict:
    """리소스 등록."""
    resource_code = data.get("resource_code", "").strip()
    resource_type = data.get("resource_type", "").strip()
    name = data.get("name", "").strip()

    if not resource_code or not resource_type or not name:
        return {"error": "resource_code, resource_type, name은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO resources
               (resource_code, resource_type, name, status, location,
                capacity, unit, current_usage)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING resource_id""",
            (resource_code, resource_type, name,
             data.get("status", "AVAILABLE"),
             data.get("location"), data.get("capacity"),
             data.get("unit"), data.get("current_usage", 0)),
        )
        resource_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "resource_id": resource_id,
                "resource_code": resource_code}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("리소스 등록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def update_resource_status(resource_id: int, data: dict) -> dict:
    """리소스 상태 변경."""
    new_status = data.get("status", "").strip()
    if not new_status:
        return {"error": "status는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sets = ["status = %s"]
        params = [new_status]
        if "current_usage" in data:
            sets.append("current_usage = %s")
            params.append(data["current_usage"])
        if "location" in data:
            sets.append("location = %s")
            params.append(data["location"])

        params.append(resource_id)
        cursor.execute(
            f"UPDATE resources SET {', '.join(sets)} WHERE resource_id = %s",
            tuple(params),
        )
        if cursor.rowcount == 0:
            cursor.close()
            return {"error": "리소스를 찾을 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True, "resource_id": resource_id, "status": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_resource_summary() -> dict:
    """리소스 현황 요약."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT resource_type, status, COUNT(*)
               FROM resources WHERE is_active = TRUE
               GROUP BY resource_type, status
               ORDER BY resource_type, status""",
        )
        rows = cursor.fetchall()

        summary: dict = {}
        for r in rows:
            rt = r[0]
            if rt not in summary:
                summary[rt] = {"type": rt, "total": 0, "by_status": {}}
            summary[rt]["by_status"][r[1]] = r[2]
            summary[rt]["total"] += r[2]

        # 평균 가동률
        cursor.execute(
            """SELECT resource_type,
                      AVG(CASE WHEN capacity > 0
                          THEN current_usage / capacity * 100 ELSE 0 END) AS avg_util
               FROM resources WHERE is_active = TRUE AND capacity > 0
               GROUP BY resource_type""",
        )
        for r in cursor.fetchall():
            if r[0] in summary:
                summary[r[0]]["avg_utilization"] = round(float(r[1]), 1)

        cursor.close()
        return {"summary": list(summary.values())}
    except Exception:
        return {"error": "요약 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
