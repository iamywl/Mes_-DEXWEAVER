"""REQ-047: 감사 추적 Audit Trail — 21 CFR Part 11 준수 (FN-062~063)."""

import json
import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def record_audit(user_id: str, action: str, entity_type: str,
                       entity_id: str = None, old_values: dict = None,
                       new_values: dict = None, ip_address: str = None,
                       reason: str = None) -> dict:
    """FN-062: 감사 이벤트 기록 (append-only)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO audit_trail
               (user_id, action, entity_type, entity_id,
                old_values, new_values, ip_address, reason)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING audit_id""",
            (user_id, action, entity_type, entity_id,
             json.dumps(old_values) if old_values else None,
             json.dumps(new_values) if new_values else None,
             ip_address, reason),
        )
        audit_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "audit_id": audit_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("감사 기록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_audit_logs(entity_type: str = None, entity_id: str = None,
                         user_id: str = None, action: str = None,
                         date_from: str = None, date_to: str = None,
                         page: int = 1, page_size: int = 50) -> dict:
    """FN-063: 감사 로그 조회 (필터 + 페이징)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        where = []
        params = []
        if entity_type:
            where.append("entity_type = %s")
            params.append(entity_type)
        if entity_id:
            where.append("entity_id = %s")
            params.append(entity_id)
        if user_id:
            where.append("user_id = %s")
            params.append(user_id)
        if action:
            where.append("action = %s")
            params.append(action)
        if date_from:
            where.append("created_at >= %s")
            params.append(date_from)
        if date_to:
            where.append("created_at <= %s")
            params.append(date_to)

        where_clause = (" WHERE " + " AND ".join(where)) if where else ""

        # 전체 건수
        cursor.execute(f"SELECT COUNT(*) FROM audit_trail{where_clause}", tuple(params))
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(
            f"""SELECT audit_id, user_id, action, entity_type, entity_id,
                       old_values, new_values, ip_address, reason, created_at
                FROM audit_trail{where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params) + (page_size, offset),
        )
        rows = cursor.fetchall()
        cursor.close()

        return {
            "items": [
                {
                    "audit_id": r[0], "user_id": r[1], "action": r[2],
                    "entity_type": r[3], "entity_id": r[4],
                    "old_values": r[5], "new_values": r[6],
                    "ip_address": r[7], "reason": r[8],
                    "created_at": r[9].isoformat() if r[9] else None,
                }
                for r in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    except Exception as e:
        log.error("감사 로그 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_audit_summary() -> dict:
    """감사 로그 요약 대시보드."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 오늘 액션별 건수
        cursor.execute(
            """SELECT action, COUNT(*)
               FROM audit_trail WHERE created_at >= CURRENT_DATE
               GROUP BY action ORDER BY COUNT(*) DESC""",
        )
        today_actions = [{"action": r[0], "count": r[1]} for r in cursor.fetchall()]

        # 엔티티 타입별 건수
        cursor.execute(
            """SELECT entity_type, COUNT(*)
               FROM audit_trail WHERE created_at >= CURRENT_DATE
               GROUP BY entity_type ORDER BY COUNT(*) DESC""",
        )
        today_entities = [{"entity_type": r[0], "count": r[1]} for r in cursor.fetchall()]

        # 전체 건수
        cursor.execute("SELECT COUNT(*) FROM audit_trail")
        total = cursor.fetchone()[0]

        cursor.close()
        return {
            "total_records": total,
            "today_by_action": today_actions,
            "today_by_entity": today_entities,
        }
    except Exception:
        return {"error": "요약 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
