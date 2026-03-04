"""REQ-048: 다국어 지원 i18n — 번역 CRUD + 로케일 조회 (FN-064)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

DEFAULT_LOCALE = "ko"


async def get_translations(locale: str = None) -> dict:
    """FN-064: 번역 리소스 조회 (locale별 key-value)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        loc = locale or DEFAULT_LOCALE
        cursor.execute(
            """SELECT msg_key, msg_value, category
               FROM translations WHERE locale = %s ORDER BY category, msg_key""",
            (loc,),
        )
        rows = cursor.fetchall()
        cursor.close()

        # 카테고리별 그룹핑
        by_cat: dict = {}
        flat: dict = {}
        for r in rows:
            flat[r[0]] = r[1]
            cat = r[2] or "general"
            if cat not in by_cat:
                by_cat[cat] = {}
            by_cat[cat][r[0]] = r[1]

        return {"locale": loc, "total": len(rows),
                "messages": flat, "by_category": by_cat}
    except Exception:
        return {"error": "번역 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_supported_locales() -> dict:
    """지원 로케일 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT locale, COUNT(*) FROM translations GROUP BY locale ORDER BY locale",
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "locales": [{"locale": r[0], "key_count": r[1]} for r in rows],
            "default": DEFAULT_LOCALE,
        }
    except Exception:
        return {"error": "로케일 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def upsert_translation(data: dict) -> dict:
    """번역 키-값 등록/수정."""
    locale = data.get("locale", "").strip()
    msg_key = data.get("msg_key", "").strip()
    msg_value = data.get("msg_value", "").strip()

    if not locale or not msg_key or not msg_value:
        return {"error": "locale, msg_key, msg_value는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO translations (locale, msg_key, msg_value, category)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (locale, msg_key)
               DO UPDATE SET msg_value = EXCLUDED.msg_value,
                             category = EXCLUDED.category""",
            (locale, msg_key, msg_value, data.get("category", "general")),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "locale": locale, "msg_key": msg_key}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("번역 등록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def delete_translation(locale: str, msg_key: str) -> dict:
    """번역 키 삭제."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM translations WHERE locale = %s AND msg_key = %s",
            (locale, msg_key),
        )
        if cursor.rowcount == 0:
            cursor.close()
            return {"error": "해당 번역 키가 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
