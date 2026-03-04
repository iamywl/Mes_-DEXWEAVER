"""REQ-041: 레시피 관리 — ISA-88 기반 레시피 등록/조회/비교 (FN-052~053)."""

import logging
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_recipe(data: dict) -> dict:
    """FN-052: 레시피 등록.

    body: { "recipe_code", "item_code", "process_code", "description",
            "parameters": [{"param_name","target_value","min_value","max_value","unit"}] }
    """
    recipe_code = data.get("recipe_code", "").strip()
    if not recipe_code:
        return {"error": "recipe_code는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 기존 버전 확인
        cursor.execute(
            "SELECT MAX(version) FROM recipes WHERE recipe_code = %s",
            (recipe_code,),
        )
        row = cursor.fetchone()
        version = (row[0] or 0) + 1

        cursor.execute(
            """INSERT INTO recipes
               (recipe_code, item_code, process_code, version, status, description)
               VALUES (%s, %s, %s, %s, 'DRAFT', %s)
               RETURNING recipe_id""",
            (recipe_code, data.get("item_code"), data.get("process_code"),
             version, data.get("description", "")),
        )
        recipe_id = cursor.fetchone()[0]

        # 파라미터 삽입
        for p in data.get("parameters", []):
            cursor.execute(
                """INSERT INTO recipe_parameters
                   (recipe_id, param_name, param_type, target_value, min_value, max_value, unit)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (recipe_id, p.get("param_name", ""), p.get("param_type", "NUMERIC"),
                 p.get("target_value"), p.get("min_value"), p.get("max_value"),
                 p.get("unit", "")),
            )

        conn.commit()
        cursor.close()
        return {"success": True, "recipe_id": recipe_id,
                "recipe_code": recipe_code, "version": version}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("레시피 등록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_recipes(item_code: str = None, process_code: str = None,
                      status: str = None) -> dict:
    """레시피 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT recipe_id, recipe_code, item_code, process_code,
                        version, status, description, approved_by, created_at
                 FROM recipes WHERE 1=1"""
        params = []
        if item_code:
            sql += " AND item_code = %s"
            params.append(item_code)
        if process_code:
            sql += " AND process_code = %s"
            params.append(process_code)
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY recipe_code, version DESC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "recipe_id": r[0], "recipe_code": r[1], "item_code": r[2],
                    "process_code": r[3], "version": r[4], "status": r[5],
                    "description": r[6], "approved_by": r[7],
                    "created_at": r[8].isoformat() if r[8] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_recipe_detail(recipe_id: int, compare_version: int = None) -> dict:
    """FN-053: 레시피 상세 조회 + 버전 비교."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT recipe_id, recipe_code, item_code, process_code,
                      version, status, description, approved_by, created_at
               FROM recipes WHERE recipe_id = %s""",
            (recipe_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": f"레시피 ID {recipe_id}를 찾을 수 없습니다."}

        recipe = {
            "recipe_id": row[0], "recipe_code": row[1], "item_code": row[2],
            "process_code": row[3], "version": row[4], "status": row[5],
            "description": row[6], "approved_by": row[7],
            "created_at": row[8].isoformat() if row[8] else None,
        }

        # 파라미터
        cursor.execute(
            """SELECT param_name, param_type, target_value, min_value, max_value, unit
               FROM recipe_parameters WHERE recipe_id = %s ORDER BY param_id""",
            (recipe_id,),
        )
        recipe["parameters"] = [
            {
                "param_name": p[0], "param_type": p[1],
                "target_value": float(p[2]) if p[2] else None,
                "min_value": float(p[3]) if p[3] else None,
                "max_value": float(p[4]) if p[4] else None,
                "unit": p[5],
            }
            for p in cursor.fetchall()
        ]

        # 버전 비교
        if compare_version:
            cursor.execute(
                """SELECT r.recipe_id FROM recipes r
                   WHERE r.recipe_code = %s AND r.version = %s""",
                (recipe["recipe_code"], compare_version),
            )
            cmp_row = cursor.fetchone()
            if cmp_row:
                cursor.execute(
                    """SELECT param_name, target_value, min_value, max_value, unit
                       FROM recipe_parameters WHERE recipe_id = %s""",
                    (cmp_row[0],),
                )
                old_params = {p[0]: p for p in cursor.fetchall()}
                diffs = []
                for np in recipe["parameters"]:
                    op = old_params.get(np["param_name"])
                    if op:
                        old_target = float(op[1]) if op[1] else None
                        if old_target != np["target_value"]:
                            diffs.append({
                                "param": np["param_name"],
                                "old_target": old_target,
                                "new_target": np["target_value"],
                            })
                    else:
                        diffs.append({"param": np["param_name"], "change": "ADDED"})
                recipe["comparison"] = {
                    "compare_version": compare_version,
                    "diffs": diffs,
                }

        cursor.close()
        return recipe
    except Exception as e:
        log.error("레시피 상세 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def approve_recipe(recipe_id: int, user_id: str) -> dict:
    """레시피 승인."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE recipes SET status = 'APPROVED', approved_by = %s
               WHERE recipe_id = %s AND status = 'DRAFT'""",
            (user_id, recipe_id),
        )
        if cursor.rowcount == 0:
            cursor.close()
            return {"error": "승인할 수 없습니다. DRAFT 상태인 레시피만 승인 가능합니다."}

        conn.commit()
        cursor.close()
        return {"success": True, "recipe_id": recipe_id, "status": "APPROVED"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
