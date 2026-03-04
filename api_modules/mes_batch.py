"""REQ-071/072: 배치실행엔진(ISA-88) + 전자배치기록(eBR)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_batch(data: dict) -> dict:
    """배치 오더 생성."""
    item_code = data.get("item_code", "").strip()
    batch_size = data.get("batch_size")
    if not item_code or batch_size is None:
        return {"error": "item_code, batch_size는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM batch_orders WHERE batch_code LIKE %s",
                       (f"BAT-{today}-%",))
        seq = (cursor.fetchone()[0] or 0) + 1
        batch_code = f"BAT-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO batch_orders
               (batch_code, recipe_id, item_code, batch_size, operator_id)
               VALUES (%s,%s,%s,%s,%s) RETURNING batch_id""",
            (batch_code, data.get("recipe_id"), item_code,
             batch_size, data.get("operator_id")),
        )
        batch_id = cursor.fetchone()[0]

        # 페이즈 자동 생성
        phases = data.get("phases", [])
        for i, p in enumerate(phases, 1):
            cursor.execute(
                """INSERT INTO batch_phases
                   (batch_id, phase_name, phase_order, params)
                   VALUES (%s,%s,%s,%s)""",
                (batch_id, p.get("name", f"Phase {i}"), i,
                 str(p.get("params", "{}"))),
            )

        conn.commit()
        cursor.close()
        return {"success": True, "batch_id": batch_id, "batch_code": batch_code,
                "phases_count": len(phases)}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("배치 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def transition_batch(batch_id: int, data: dict) -> dict:
    """배치 상태 전이 (ISA-88 State Machine)."""
    new_status = data.get("status", "").strip()
    valid = {"IDLE": ["RUNNING"],
             "RUNNING": ["HELD", "COMPLETE", "ABORTED"],
             "HELD": ["RUNNING", "ABORTED"]}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM batch_orders WHERE batch_id = %s",
                       (batch_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": "배치를 찾을 수 없습니다."}

        current = row[0]
        if new_status not in valid.get(current, []):
            cursor.close()
            return {"error": f"{current} → {new_status} 전이 불가"}

        sets = ["status = %s"]
        params = [new_status]
        if new_status == "RUNNING" and current == "IDLE":
            sets.append("started_at = NOW()")
        elif new_status in ("COMPLETE", "ABORTED"):
            sets.append("completed_at = NOW()")

        params.append(batch_id)
        cursor.execute(
            f"UPDATE batch_orders SET {', '.join(sets)} WHERE batch_id = %s",
            tuple(params),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "batch_id": batch_id,
                "prev": current, "new": new_status}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_batches(status: str = None) -> dict:
    """배치 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = """SELECT batch_id, batch_code, item_code, batch_size,
                        status, current_phase, started_at, completed_at,
                        operator_id, created_at
                 FROM batch_orders WHERE 1=1"""
        params = []
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT 200"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"batch_id": r[0], "batch_code": r[1], "item_code": r[2],
                 "batch_size": float(r[3]) if r[3] else 0,
                 "status": r[4], "current_phase": r[5],
                 "started_at": r[6].isoformat() if r[6] else None,
                 "completed_at": r[7].isoformat() if r[7] else None,
                 "operator_id": r[8],
                 "created_at": r[9].isoformat() if r[9] else None}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def add_ebr_record(batch_id: int, data: dict) -> dict:
    """eBR 기록 추가."""
    record_type = data.get("record_type", "EVENT")

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO ebr_records
               (batch_id, record_type, phase_id, param_name, param_value,
                recorded_by, notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING ebr_id""",
            (batch_id, record_type, data.get("phase_id"),
             data.get("param_name"), data.get("param_value"),
             data.get("recorded_by"), data.get("notes")),
        )
        ebr_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "ebr_id": ebr_id}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_ebr(batch_id: int) -> dict:
    """배치의 eBR 기록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT ebr_id, record_type, phase_id, param_name, param_value,
                      recorded_by, recorded_at, notes
               FROM ebr_records WHERE batch_id = %s
               ORDER BY recorded_at""",
            (batch_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "batch_id": batch_id,
            "records": [
                {"ebr_id": r[0], "record_type": r[1], "phase_id": r[2],
                 "param_name": r[3], "param_value": r[4],
                 "recorded_by": r[5],
                 "recorded_at": r[6].isoformat() if r[6] else None,
                 "notes": r[7]}
                for r in rows
            ],
            "total": len(rows),
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
