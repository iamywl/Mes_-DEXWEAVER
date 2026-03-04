"""REQ-075: 멀티사이트 관리 — ISA-95 계층, 사이트별 통합 가시성."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_site(data: dict) -> dict:
    """사이트 등록."""
    site_code = data.get("site_code", "").strip()
    site_name = data.get("site_name", "").strip()
    if not site_code or not site_name:
        return {"error": "site_code, site_name은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO sites
               (site_code, site_name, site_type, parent_site_id, timezone, address)
               VALUES (%s,%s,%s,%s,%s,%s) RETURNING site_id""",
            (site_code, site_name, data.get("site_type", "FACTORY"),
             data.get("parent_site_id"), data.get("timezone", "Asia/Seoul"),
             data.get("address")),
        )
        site_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "site_id": site_id, "site_code": site_code}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_sites() -> dict:
    """사이트 목록 (ISA-95 계층 트리)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT site_id, site_code, site_name, site_type,
                      parent_site_id, timezone, address, is_active
               FROM sites WHERE is_active = TRUE
               ORDER BY site_type, site_code""",
        )
        rows = cursor.fetchall()
        cursor.close()

        flat = [
            {"site_id": r[0], "site_code": r[1], "site_name": r[2],
             "site_type": r[3], "parent_site_id": r[4],
             "timezone": r[5], "address": r[6]}
            for r in rows
        ]

        # 트리 구조 생성
        by_id = {s["site_id"]: {**s, "children": []} for s in flat}
        roots = []
        for s in flat:
            pid = s["parent_site_id"]
            if pid and pid in by_id:
                by_id[pid]["children"].append(by_id[s["site_id"]])
            else:
                roots.append(by_id[s["site_id"]])

        return {"sites": flat, "tree": roots, "total": len(flat)}
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_site_dashboard(site_id: int) -> dict:
    """사이트별 통합 현황."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT site_code, site_name FROM sites WHERE site_id = %s",
                       (site_id,))
        site = cursor.fetchone()
        if not site:
            cursor.close()
            return {"error": "사이트를 찾을 수 없습니다."}

        # 기본 통계 (전체 — 사이트 필터는 확장 시 적용)
        cursor.execute("SELECT COUNT(*) FROM equipments WHERE status = 'RUNNING'")
        running = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'IN_PROGRESS'")
        active_wo = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM inspections WHERE created_at >= CURRENT_DATE")
        today_insp = cursor.fetchone()[0]

        cursor.close()
        return {
            "site_id": site_id, "site_code": site[0], "site_name": site[1],
            "running_equipments": running,
            "active_work_orders": active_wo,
            "today_inspections": today_insp,
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
