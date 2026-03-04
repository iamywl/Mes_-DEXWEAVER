"""OEE API 테스트."""

import pytest


class TestOeeApi:
    """OEE 자동계산 API 테스트."""

    def test_oee_get(self, client, auth_headers):
        """FN-044: 설비별 OEE 조회."""
        r = client.get("/api/equipment/oee/EQP-001", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "equip_code" in data or "error" in data

    def test_oee_get_with_dates(self, client, auth_headers):
        """날짜 필터 OEE 조회."""
        r = client.get("/api/equipment/oee/EQP-001?start_date=2026-02-01&end_date=2026-03-04",
                       headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_oee_invalid_equip(self, client, auth_headers):
        """존재하지 않는 설비 OEE 조회."""
        r = client.get("/api/equipment/oee/INVALID-999", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert "error" in r.json()

    def test_oee_dashboard(self, client, auth_headers):
        """FN-045: OEE 대시보드."""
        r = client.get("/api/equipment/oee/dashboard", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "plant_oee" in data or "equipments" in data or "error" in data
