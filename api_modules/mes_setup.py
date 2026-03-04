"""REQ-067: 셋업시간 매트릭스 — 제품간 전환 셋업, 순서 의존 모델링."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def upsert_setup(data: dict) -> dict:
    """셋업시간 등록/수정."""
    equip_code = data.get("equip_code", "").strip()
    from_item = data.get("from_item_code", "").strip()
    to_item = data.get("to_item_code", "").strip()
    planned = data.get("planned_minutes")

    if not equip_code or not from_item or not to_item or planned is None:
        return {"error": "equip_code, from_item_code, to_item_code, planned_minutes는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO setup_matrix
               (equip_code, from_item_code, to_item_code, planned_minutes)
               VALUES (%s,%s,%s,%s)
               ON CONFLICT (equip_code, from_item_code, to_item_code)
               DO UPDATE SET planned_minutes = EXCLUDED.planned_minutes,
                             updated_at = NOW()
               RETURNING setup_id""",
            (equip_code, from_item, to_item, planned),
        )
        setup_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "setup_id": setup_id}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def record_actual(data: dict) -> dict:
    """실제 셋업시간 기록 (평균 자동 갱신)."""
    equip_code = data.get("equip_code", "").strip()
    from_item = data.get("from_item_code", "").strip()
    to_item = data.get("to_item_code", "").strip()
    actual = data.get("actual_minutes")

    if not equip_code or not from_item or not to_item or actual is None:
        return {"error": "필수 파라미터가 누락되었습니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 이동평균 업데이트
        cursor.execute(
            """UPDATE setup_matrix SET
                 actual_avg_minutes = COALESCE(
                   (actual_avg_minutes * sample_count + %s) / (sample_count + 1),
                   %s),
                 sample_count = sample_count + 1,
                 updated_at = NOW()
               WHERE equip_code = %s AND from_item_code = %s AND to_item_code = %s""",
            (actual, actual, equip_code, from_item, to_item),
        )
        if cursor.rowcount == 0:
            # 없으면 신규 생성
            cursor.execute(
                """INSERT INTO setup_matrix
                   (equip_code, from_item_code, to_item_code, planned_minutes,
                    actual_avg_minutes, sample_count)
                   VALUES (%s,%s,%s,%s,%s,1)""",
                (equip_code, from_item, to_item, actual, actual),
            )
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


async def get_matrix(equip_code: str = None) -> dict:
    """셋업시간 매트릭스 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT setup_id, equip_code, from_item_code, to_item_code,
                        planned_minutes, actual_avg_minutes, sample_count
                 FROM setup_matrix WHERE 1=1"""
        params = []
        if equip_code:
            sql += " AND equip_code = %s"
            params.append(equip_code)
        sql += " ORDER BY equip_code, from_item_code, to_item_code"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        # 설비별 그룹핑
        by_equip: dict = {}
        for r in rows:
            eq = r[1]
            if eq not in by_equip:
                by_equip[eq] = []
            diff = None
            if r[4] and r[5]:
                diff = round(float(r[5]) - float(r[4]), 1)
            by_equip[eq].append({
                "from": r[2], "to": r[3],
                "planned": r[4], "actual_avg": float(r[5]) if r[5] else None,
                "samples": r[6], "variance": diff,
            })

        return {"matrix": by_equip, "total_entries": len(rows)}
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
