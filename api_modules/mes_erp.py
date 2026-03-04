"""REQ-045: ERP 연동 — 동기화 설정, 실행, 이력 조회 (FN-059)."""

import json
import logging
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_sync_config(data: dict) -> dict:
    """ERP 동기화 설정 생성."""
    erp_type = data.get("erp_type", "").strip()
    connection_url = data.get("connection_url", "").strip()
    entity_type = data.get("entity_type", "").strip()

    if not erp_type or not connection_url or not entity_type:
        return {"error": "erp_type, connection_url, entity_type는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO erp_sync_config
               (erp_type, connection_url, sync_direction, entity_type,
                mapping_config, sync_interval_min, is_active)
               VALUES (%s, %s, %s, %s, %s::jsonb, %s, TRUE)
               RETURNING sync_id""",
            (erp_type, connection_url,
             data.get("sync_direction", "INBOUND"), entity_type,
             json.dumps(data.get("mapping_config", {})),
             data.get("sync_interval_min", 60)),
        )
        sync_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "sync_id": sync_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("ERP 동기화 설정 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_sync_configs() -> dict:
    """ERP 동기화 설정 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT sync_id, erp_type, connection_url, sync_direction,
                      entity_type, mapping_config, sync_interval_min,
                      is_active, created_at
               FROM erp_sync_config ORDER BY created_at DESC""",
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "sync_id": r[0], "erp_type": r[1],
                    "connection_url": r[2], "sync_direction": r[3],
                    "entity_type": r[4], "mapping_config": r[5] or {},
                    "sync_interval_min": r[6], "is_active": r[7],
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


async def execute_sync(data: dict) -> dict:
    """ERP 동기화 즉시 실행 (시뮬레이션)."""
    sync_id = data.get("sync_id")
    if not sync_id:
        return {"error": "sync_id는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            "SELECT entity_type, sync_direction FROM erp_sync_config WHERE sync_id = %s",
            (sync_id,),
        )
        cfg = cursor.fetchone()
        if not cfg:
            cursor.close()
            return {"error": f"동기화 설정 {sync_id}를 찾을 수 없습니다."}

        # 시뮬레이션: 실제 ERP 연동 대신 로그 기록
        processed = data.get("records_count", 10)
        failed = 0

        cursor.execute(
            """INSERT INTO erp_sync_log
               (sync_id, direction, entity_type, records_processed,
                records_success, records_failed, error_detail)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING log_id""",
            (sync_id, cfg[1], cfg[0], processed,
             processed - failed, failed, None),
        )
        log_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {
            "success": True, "log_id": log_id,
            "records_processed": processed,
            "records_success": processed - failed,
            "records_failed": failed,
        }
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("ERP 동기화 실행 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_sync_logs(sync_id: int = None) -> dict:
    """동기화 이력 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT log_id, sync_id, direction, entity_type,
                        records_processed, records_success, records_failed,
                        error_detail, synced_at
                 FROM erp_sync_log WHERE 1=1"""
        params = []
        if sync_id:
            sql += " AND sync_id = %s"
            params.append(sync_id)
        sql += " ORDER BY synced_at DESC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "log_id": r[0], "sync_id": r[1], "direction": r[2],
                    "entity_type": r[3], "records_processed": r[4],
                    "records_success": r[5], "records_failed": r[6],
                    "error_detail": r[7],
                    "synced_at": r[8].isoformat() if r[8] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
