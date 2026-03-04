"""NFR-017: 전자서명 — FDA 21 CFR Part 11 준수.

요구사항:
  1. 2개 식별요소 (ID + PW 재인증)
  2. 서명 표시 (서명자명 + 일시 + 의미)
  3. 서명-기록 암호화 연결 (SHA-256 해시 바인딩)
  4. 재사용/양도 불가 (1회성 서명, 취소 가능)
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# bcrypt import (graceful fallback)
try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False
    log.warning("bcrypt 미설치 — 전자서명 비밀번호 검증 비활성화")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """bcrypt 비밀번호 검증."""
    if not _HAS_BCRYPT:
        return plain_password == hashed_password
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def _compute_signature_hash(user_id: str, entity_type: str, entity_id: str,
                            meaning: str, signed_at: str, nonce: str) -> str:
    """서명-기록 암호화 연결 — SHA-256 해시 바인딩.

    서명자, 대상 레코드, 의미, 시각, 1회용 nonce를 결합하여
    재사용/위변조가 불가능한 해시를 생성합니다.
    """
    payload = f"{user_id}|{entity_type}|{entity_id}|{meaning}|{signed_at}|{nonce}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def sign_record(user_id: str, password: str, entity_type: str,
                      entity_id: str, meaning: str, ip_address: str = None,
                      record_snapshot: dict = None) -> dict:
    """전자서명 생성 — 2요소 인증(ID+PW) 후 서명 해시 생성.

    Args:
        user_id: 서명자 ID
        password: 비밀번호 (재인증)
        entity_type: 대상 레코드 유형 (inspection, work_order, recipe 등)
        entity_id: 대상 레코드 ID
        meaning: 서명 의미 (APPROVED, REVIEWED, VERIFIED, RELEASED 등)
        ip_address: 클라이언트 IP
        record_snapshot: 서명 시점의 레코드 상태 스냅샷 (JSON)
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 1. 사용자 존재 확인 + 비밀번호 가져오기
        cursor.execute(
            "SELECT user_id, name, password FROM users WHERE user_id = %s",
            (user_id,),
        )
        user_row = cursor.fetchone()
        if not user_row:
            cursor.close()
            return {"error": "사용자를 찾을 수 없습니다.", "_status": 404}

        user_name = user_row[1]
        stored_pw = user_row[2]

        # 2. 비밀번호 재인증 (2요소: ID + PW)
        if not _verify_password(password, stored_pw):
            cursor.close()
            # 감사 로그: 서명 실패 기록
            log.warning("전자서명 비밀번호 검증 실패: user=%s entity=%s/%s",
                        user_id, entity_type, entity_id)
            return {"error": "비밀번호가 일치하지 않습니다. 전자서명이 거부되었습니다.",
                    "_status": 401}

        # 3. 서명 해시 생성
        signed_at = datetime.now(timezone.utc).isoformat()
        # nonce: 서명 시점의 레코드 해시로 1회성 보장
        nonce_data = json.dumps(record_snapshot, sort_keys=True) if record_snapshot else signed_at
        nonce = hashlib.sha256(nonce_data.encode("utf-8")).hexdigest()[:16]

        signature_hash = _compute_signature_hash(
            user_id, entity_type, entity_id, meaning, signed_at, nonce)

        # 4. DB 저장
        cursor.execute(
            """INSERT INTO electronic_signatures
               (user_id, user_name, entity_type, entity_id, meaning,
                signature_hash, nonce, record_snapshot, ip_address)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING signature_id, signed_at""",
            (user_id, user_name, entity_type, entity_id, meaning,
             signature_hash, nonce,
             json.dumps(record_snapshot) if record_snapshot else None,
             ip_address),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()

        return {
            "success": True,
            "signature_id": row[0],
            "signed_at": row[1].isoformat() if row[1] else signed_at,
            "signer": user_name,
            "meaning": meaning,
            "signature_hash": signature_hash,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("전자서명 생성 오류: %s", e)
        return {"error": f"전자서명 생성 중 오류가 발생했습니다: {e}"}
    finally:
        if conn:
            release_conn(conn)


async def verify_signature(signature_id: int) -> dict:
    """전자서명 무결성 검증 — 저장된 해시와 재계산 해시 비교."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT signature_id, user_id, user_name, entity_type, entity_id,
                      meaning, signature_hash, nonce, signed_at, revoked
               FROM electronic_signatures WHERE signature_id = %s""",
            (signature_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return {"error": "전자서명을 찾을 수 없습니다.", "_status": 404}

        sig_id, uid, uname, etype, eid, meaning, stored_hash, nonce, sat, revoked = row

        if revoked:
            return {
                "verified": False,
                "reason": "REVOKED",
                "signature_id": sig_id,
                "message": "이 전자서명은 취소되었습니다.",
            }

        # 해시 재계산
        expected_hash = _compute_signature_hash(
            uid, etype, eid, meaning, sat.isoformat() if sat else "", nonce or "")

        verified = (stored_hash == expected_hash)

        return {
            "verified": verified,
            "signature_id": sig_id,
            "signer": uname,
            "meaning": meaning,
            "signed_at": sat.isoformat() if sat else None,
            "entity_type": etype,
            "entity_id": eid,
            "integrity": "VALID" if verified else "TAMPERED",
        }
    except Exception as e:
        log.error("전자서명 검증 오류: %s", e)
        return {"error": f"검증 중 오류: {e}"}
    finally:
        if conn:
            release_conn(conn)


async def get_signature_history(entity_type: str = None, entity_id: str = None,
                                user_id: str = None, page: int = 1,
                                page_size: int = 50) -> dict:
    """전자서명 이력 조회."""
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

        where_clause = (" WHERE " + " AND ".join(where)) if where else ""

        cursor.execute(
            f"SELECT COUNT(*) FROM electronic_signatures{where_clause}",
            tuple(params),
        )
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(
            f"""SELECT signature_id, user_id, user_name, entity_type, entity_id,
                       meaning, signature_hash, signed_at, revoked, revoked_reason
                FROM electronic_signatures{where_clause}
                ORDER BY signed_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params) + (page_size, offset),
        )
        rows = cursor.fetchall()
        cursor.close()

        return {
            "items": [
                {
                    "signature_id": r[0], "user_id": r[1], "user_name": r[2],
                    "entity_type": r[3], "entity_id": r[4], "meaning": r[5],
                    "signature_hash": r[6],
                    "signed_at": r[7].isoformat() if r[7] else None,
                    "revoked": r[8], "revoked_reason": r[9],
                }
                for r in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        log.error("전자서명 이력 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def revoke_signature(signature_id: int, user_id: str,
                           reason: str) -> dict:
    """전자서명 취소 (관리자 전용) — 서명 자체는 보존, revoked 플래그 설정."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            "SELECT revoked FROM electronic_signatures WHERE signature_id = %s",
            (signature_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": "전자서명을 찾을 수 없습니다.", "_status": 404}
        if row[0]:
            cursor.close()
            return {"error": "이미 취소된 전자서명입니다."}

        cursor.execute(
            """UPDATE electronic_signatures
               SET revoked = TRUE, revoked_reason = %s, revoked_at = NOW(),
                   revoked_by = %s
               WHERE signature_id = %s""",
            (reason, user_id, signature_id),
        )
        conn.commit()
        cursor.close()

        return {"success": True, "message": "전자서명이 취소되었습니다."}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("전자서명 취소 오류: %s", e)
        return {"error": f"취소 중 오류: {e}"}
    finally:
        if conn:
            release_conn(conn)
