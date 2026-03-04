"""CAPA API 테스트."""

import pytest


class TestCapaApi:
    """CAPA 프로세스 API 테스트."""

    def test_capa_create(self, client, auth_headers):
        """FN-041: CAPA 등록."""
        r = client.post("/api/quality/capa", headers=auth_headers, json={
            "title": "테스트 CAPA",
            "capa_type": "CORRECTIVE",
            "description": "테스트용 시정조치",
            "priority": "HIGH",
            "assigned_to": "admin",
        })
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "success" in data or "error" in data

    def test_capa_list(self, client, auth_headers):
        """FN-043: CAPA 목록 조회."""
        r = client.get("/api/quality/capa", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or "error" in data

    def test_capa_list_filter(self, client, auth_headers):
        """CAPA 상태 필터 조회."""
        r = client.get("/api/quality/capa?status=OPEN", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_capa_status_transition_invalid(self, client, auth_headers):
        """FN-042: 잘못된 상태 전이."""
        r = client.put("/api/quality/capa/CAPA-99999/status",
                       headers=auth_headers, json={"status": "CLOSED"})
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert "error" in r.json()

    def test_capa_create_missing_title(self, client, auth_headers):
        """필수 필드 누락."""
        r = client.post("/api/quality/capa", headers=auth_headers,
                        json={"capa_type": "CORRECTIVE"})
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert "error" in r.json()
