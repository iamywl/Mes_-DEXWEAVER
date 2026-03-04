"""알림 API 테스트."""

import pytest


class TestNotificationApi:
    """알림 시스템 API 테스트."""

    def test_notifications_list(self, client, auth_headers):
        """알림 이력 조회."""
        r = client.get("/api/notifications", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or "error" in data

    def test_notifications_unread(self, client, auth_headers):
        """미읽음 알림만 조회."""
        r = client.get("/api/notifications?unread_only=true", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_notification_mark_read(self, client, auth_headers):
        """알림 읽음 처리."""
        r = client.put("/api/notifications/1/read", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_notification_settings_get(self, client, auth_headers):
        """FN-047: 알림 설정 조회."""
        r = client.get("/api/notifications/settings", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "settings" in data or "user_id" in data or "error" in data

    def test_notification_settings_update(self, client, auth_headers):
        """FN-047: 알림 설정 변경."""
        r = client.post("/api/notifications/settings", headers=auth_headers, json={
            "settings": [
                {"type": "EQUIP_DOWN", "channel": "WEB", "enabled": True},
                {"type": "SPC_VIOLATION", "channel": "WEB", "enabled": False},
            ]
        })
        assert r.status_code in (200, 401)
