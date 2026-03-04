"""REQ-053: 전자 작업지시서 (Electronic Work Instruction) 관리."""

import logging
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_work_instruction(data: dict) -> dict:
    """작업지시서 생성.

    body: { "wo_no": "WO-...", "title": "...", "process_code": "PRC-001",
            "steps": [{"step_no":1, "title":"...", "description":"...", "duration_min":10}] }
    """
    wo_no = data.get("wo_no", "").strip()
    title = data.get("title", "").strip()
    process_code = data.get("process_code", "")
    steps = data.get("steps", [])

    if not title:
        return {"error": "title은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # ID 생성
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT COUNT(*) FROM work_instructions WHERE wi_id LIKE %s",
            (f"WI-{today}-%",),
        )
        seq = (cursor.fetchone()[0] or 0) + 1
        wi_id = f"WI-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO work_instructions
               (wi_id, wo_no, title, process_code, version, status, created_at)
               VALUES (%s, %s, %s, %s, 1, 'DRAFT', NOW())""",
            (wi_id, wo_no or None, title, process_code or None),
        )

        # 단계 삽입
        for step in steps:
            step_no = step.get("step_no", 0)
            cursor.execute(
                """INSERT INTO work_instruction_steps
                   (wi_id, step_no, title, description, duration_min, sign_required)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (wi_id, step_no, step.get("title", ""),
                 step.get("description", ""), step.get("duration_min", 0),
                 step.get("sign_required", True)),
            )

        conn.commit()
        cursor.close()
        return {"success": True, "wi_id": wi_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("작업지시서 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_work_instructions(wo_no: str = None, status: str = None) -> dict:
    """작업지시서 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT wi_id, wo_no, title, process_code, version, status, created_at
                 FROM work_instructions WHERE 1=1"""
        params = []
        if wo_no:
            sql += " AND wo_no = %s"
            params.append(wo_no)
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT 100"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "wi_id": r[0], "wo_no": r[1], "title": r[2],
                    "process_code": r[3], "version": r[4], "status": r[5],
                    "created_at": r[6].isoformat() if r[6] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_work_instruction_detail(wi_id: str) -> dict:
    """작업지시서 상세 (단계 포함)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT wi_id, wo_no, title, process_code, version, status, created_at
               FROM work_instructions WHERE wi_id = %s""",
            (wi_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": f"작업지시서 '{wi_id}'를 찾을 수 없습니다."}

        wi = {
            "wi_id": row[0], "wo_no": row[1], "title": row[2],
            "process_code": row[3], "version": row[4], "status": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
        }

        cursor.execute(
            """SELECT step_no, title, description, duration_min,
                      sign_required, signed_by, signed_at
               FROM work_instruction_steps
               WHERE wi_id = %s ORDER BY step_no""",
            (wi_id,),
        )
        steps = cursor.fetchall()
        wi["steps"] = [
            {
                "step_no": s[0], "title": s[1], "description": s[2],
                "duration_min": s[3], "sign_required": s[4],
                "signed_by": s[5],
                "signed_at": s[6].isoformat() if s[6] else None,
            }
            for s in steps
        ]

        cursor.close()
        return wi
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def sign_step(wi_id: str, step_no: int, user_id: str) -> dict:
    """작업지시서 단계 전자서명."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE work_instruction_steps
               SET signed_by = %s, signed_at = NOW()
               WHERE wi_id = %s AND step_no = %s AND signed_by IS NULL""",
            (user_id, wi_id, step_no),
        )
        if cursor.rowcount == 0:
            cursor.close()
            return {"error": "서명할 수 없습니다. 이미 서명되었거나 존재하지 않는 단계입니다."}

        # 모든 단계 서명 완료 확인
        cursor.execute(
            """SELECT COUNT(*) FROM work_instruction_steps
               WHERE wi_id = %s AND sign_required = true AND signed_by IS NULL""",
            (wi_id,),
        )
        unsigned = cursor.fetchone()[0]
        if unsigned == 0:
            cursor.execute(
                "UPDATE work_instructions SET status = 'COMPLETED' WHERE wi_id = %s",
                (wi_id,),
            )

        conn.commit()
        cursor.close()
        return {"success": True, "wi_id": wi_id, "step_no": step_no,
                "all_signed": unsigned == 0}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("단계 서명 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
