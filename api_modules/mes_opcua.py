"""REQ-046: OPC-UA 연동 — 서버 설정, 노드 구독, 상태 모니터링 (FN-060~061)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def save_opcua_config(data: dict) -> dict:
    """OPC-UA 설정 저장."""
    server_url = data.get("server_url", "").strip()
    equip_code = data.get("equip_code", "").strip()
    node_id = data.get("node_id", "").strip()
    sensor_type = data.get("sensor_type", "").strip()

    if not server_url or not equip_code or not node_id or not sensor_type:
        return {"error": "server_url, equip_code, node_id, sensor_type는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO opcua_config
               (server_url, equip_code, node_id, sensor_type,
                subscribe_interval_ms, is_active)
               VALUES (%s, %s, %s, %s, %s, TRUE)
               RETURNING config_id""",
            (server_url, equip_code, node_id, sensor_type,
             data.get("subscribe_interval_ms", 1000)),
        )
        config_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "config_id": config_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("OPC-UA 설정 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_opcua_configs() -> dict:
    """OPC-UA 설정 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT config_id, server_url, equip_code, node_id, sensor_type,
                      subscribe_interval_ms, is_active, created_at
               FROM opcua_config ORDER BY created_at DESC""",
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "config_id": r[0], "server_url": r[1], "equip_code": r[2],
                    "node_id": r[3], "sensor_type": r[4],
                    "subscribe_interval_ms": r[5], "is_active": r[6],
                    "created_at": r[7].isoformat() if r[7] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_opcua_status() -> dict:
    """OPC-UA 연결 상태 대시보드."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM opcua_config WHERE is_active = TRUE")
        active = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM opcua_config")
        total = cursor.fetchone()[0]

        # 최근 수집 상태
        cursor.execute(
            """SELECT equip_code, MAX(collected_at) AS last_received
               FROM sensor_data WHERE source = 'OPCUA'
               GROUP BY equip_code ORDER BY last_received DESC LIMIT 20""",
        )
        recent = [
            {"equip_code": r[0], "last_received": r[1].isoformat() if r[1] else None}
            for r in cursor.fetchall()
        ]

        cursor.close()
        return {
            "total_configs": total,
            "active_configs": active,
            "status": "CONNECTED" if active > 0 else "DISCONNECTED",
            "recent_data": recent,
        }
    except Exception:
        return {"error": "상태 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
