"""FN-046~047: 실시간 알림 — WebSocket + REST API."""

import json
import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


# ── WebSocket Connection Manager ─────────────────────────────
class ConnectionManager:
    """WebSocket 연결 관리."""

    def __init__(self):
        self.active: dict[str, list] = {}  # user_id → [websocket, ...]

    async def connect(self, websocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active:
            self.active[user_id] = []
        self.active[user_id].append(websocket)
        log.info("WS connected: %s (total: %d)", user_id,
                 sum(len(v) for v in self.active.values()))

    def disconnect(self, websocket, user_id: str):
        if user_id in self.active:
            self.active[user_id] = [w for w in self.active[user_id] if w != websocket]
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """특정 사용자에게 알림 전송."""
        if user_id in self.active:
            data = json.dumps(message, default=str, ensure_ascii=False)
            for ws in self.active[user_id]:
                try:
                    await ws.send_text(data)
                except Exception:
                    pass

    async def broadcast(self, message: dict, exclude_user: str = None):
        """전체 사용자에게 브로드캐스트."""
        data = json.dumps(message, default=str, ensure_ascii=False)
        for user_id, connections in self.active.items():
            if user_id == exclude_user:
                continue
            for ws in connections:
                try:
                    await ws.send_text(data)
                except Exception:
                    pass

    @property
    def connected_users(self):
        return list(self.active.keys())


manager = ConnectionManager()


# ── 알림 생성 + 전송 ─────────────────────────────────────────
async def create_notification(user_id: str, notif_type: str, title: str,
                                message: str = None, severity: str = "INFO",
                                ref_type: str = None, ref_id: str = None) -> dict:
    """알림 생성 → DB 저장 + WebSocket 전송."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO notifications (user_id, type, title, message, severity, ref_type, ref_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING notification_id""",
            (user_id, notif_type, title, message, severity, ref_type, ref_id))
        notif_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()

        # WebSocket으로 실시간 전송
        payload = {
            "notification_id": notif_id,
            "type": notif_type,
            "title": title,
            "message": message,
            "severity": severity,
            "ref_type": ref_type,
            "ref_id": ref_id,
        }
        await manager.send_to_user(user_id, payload)
        return {"success": True, "notification_id": notif_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("Notification creation error: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_notifications(user_id: str, unread_only: bool = False,
                              limit: int = 50) -> dict:
    """알림 이력 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT notification_id, type, title, message, severity,
                        ref_type, ref_id, is_read, created_at
                 FROM notifications WHERE user_id = %s"""
        params = [user_id]
        if unread_only:
            sql += " AND is_read = FALSE"
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        # 미읽음 개수
        cursor.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
            (user_id,))
        unread_count = cursor.fetchone()[0]

        items = [{
            "notification_id": r[0], "type": r[1], "title": r[2],
            "message": r[3], "severity": r[4], "ref_type": r[5],
            "ref_id": r[6], "is_read": r[7],
            "created_at": str(r[8]) if r[8] else None,
        } for r in rows]

        cursor.close()
        return {"items": items, "total": len(items), "unread_count": unread_count}
    except Exception as e:
        log.error("Notification list error: %s", e)
        return {"error": "알림 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def mark_read(notification_id: int) -> dict:
    """알림 읽음 처리."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE notification_id = %s",
            (notification_id,))
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


async def get_notification_settings(user_id: str) -> dict:
    """FN-047: 알림 설정 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "SELECT notification_type, channel, is_enabled "
            "FROM notification_settings WHERE user_id = %s",
            (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        return {"user_id": user_id,
                "settings": [{"type": r[0], "channel": r[1], "enabled": r[2]} for r in rows]}
    except Exception:
        return {"error": "알림 설정 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def update_notification_settings(user_id: str, data: dict) -> dict:
    """FN-047: 알림 설정 변경."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        settings = data.get("settings", [])
        for s in settings:
            cursor.execute(
                """INSERT INTO notification_settings (user_id, notification_type, channel, is_enabled)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (user_id, notification_type, channel) DO UPDATE SET
                       is_enabled = EXCLUDED.is_enabled""",
                (user_id, s["type"], s.get("channel", "WEB"), s.get("enabled", True)))
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
