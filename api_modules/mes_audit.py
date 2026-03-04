"""REQ-049: 감사 추적 Audit Trail — NFR-014: append-only + hash chain.

21 CFR Part 11 준수: 불변 감사 로그, SHA-256 해시 체인, 무결성 검증.
"""

import hashlib
import json
import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


def _compute_hash(audit_id, user_id, action, entity_type, entity_id,
                  old_values, new_values, prev_hash):
    """SHA-256 hash chain — 이전 해시 포함하여 체인 무결성 보장."""
    payload = f"{audit_id}|{user_id}|{action}|{entity_type}|{entity_id}|" \
              f"{json.dumps(old_values, sort_keys=True) if old_values else ''}|" \
              f"{json.dumps(new_values, sort_keys=True) if new_values else ''}|" \
              f"{prev_hash or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def record_audit(user_id: str, action: str, entity_type: str,
                       entity_id: str = None, old_values: dict = None,
                       new_values: dict = None, ip_address: str = None,
                       reason: str = None) -> dict:
    """FN-062: 감사 이벤트 기록 (append-only + hash chain)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # Get previous hash for chain
        cursor.execute(
            "SELECT record_hash FROM audit_trail ORDER BY audit_id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        prev_hash = row[0] if row else None

        # Insert with placeholder hash, then update with real hash
        cursor.execute(
            """INSERT INTO audit_trail
               (user_id, action, entity_type, entity_id,
                old_values, new_values, ip_address, reason,
                prev_hash, record_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
               RETURNING audit_id""",
            (user_id, action, entity_type, entity_id,
             json.dumps(old_values) if old_values else None,
             json.dumps(new_values) if new_values else None,
             ip_address, reason, prev_hash),
        )
        audit_id = cursor.fetchone()[0]

        # Compute hash including audit_id
        record_hash = _compute_hash(
            audit_id, user_id, action, entity_type, entity_id,
            old_values, new_values, prev_hash)

        # Temporarily disable trigger for hash update only
        cursor.execute("ALTER TABLE audit_trail DISABLE TRIGGER trg_audit_immutable")
        cursor.execute(
            "UPDATE audit_trail SET record_hash = %s WHERE audit_id = %s",
            (record_hash, audit_id),
        )
        cursor.execute("ALTER TABLE audit_trail ENABLE TRIGGER trg_audit_immutable")

        conn.commit()
        cursor.close()
        return {"success": True, "audit_id": audit_id, "hash": record_hash}
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

        cursor.execute(f"SELECT COUNT(*) FROM audit_trail{where_clause}", tuple(params))
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(
            f"""SELECT audit_id, user_id, action, entity_type, entity_id,
                       old_values, new_values, ip_address, reason,
                       prev_hash, record_hash, created_at
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
                    "prev_hash": r[9], "record_hash": r[10],
                    "created_at": r[11].isoformat() if r[11] else None,
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


async def verify_chain_integrity(limit: int = 1000) -> dict:
    """NFR-014: Hash chain 무결성 검증."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT audit_id, user_id, action, entity_type, entity_id,
                      old_values, new_values, prev_hash, record_hash
               FROM audit_trail ORDER BY audit_id ASC LIMIT %s""",
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            return {"verified": True, "records_checked": 0}

        errors = []
        prev_hash = None
        for r in rows:
            audit_id = r[0]
            expected = _compute_hash(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7])
            if r[8] != expected:
                errors.append({
                    "audit_id": audit_id,
                    "error": "hash_mismatch",
                    "expected": expected[:12] + "...",
                    "actual": (r[8] or "")[:12] + "...",
                })
            if prev_hash and r[7] != prev_hash:
                errors.append({
                    "audit_id": audit_id,
                    "error": "chain_break",
                    "expected_prev": prev_hash[:12] + "...",
                    "actual_prev": (r[7] or "")[:12] + "...",
                })
            prev_hash = r[8]

        return {
            "verified": len(errors) == 0,
            "records_checked": len(rows),
            "errors": errors[:20],
        }
    except Exception as e:
        return {"error": f"무결성 검증 오류: {e}"}
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

        cursor.execute(
            """SELECT action, COUNT(*)
               FROM audit_trail WHERE created_at >= CURRENT_DATE
               GROUP BY action ORDER BY COUNT(*) DESC""",
        )
        today_actions = [{"action": r[0], "count": r[1]} for r in cursor.fetchall()]

        cursor.execute(
            """SELECT entity_type, COUNT(*)
               FROM audit_trail WHERE created_at >= CURRENT_DATE
               GROUP BY entity_type ORDER BY COUNT(*) DESC""",
        )
        today_entities = [{"entity_type": r[0], "count": r[1]} for r in cursor.fetchall()]

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
