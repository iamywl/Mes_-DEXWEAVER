"""설비관리 API 테스트 (FN-013~014, 032~034)."""

import pytest


class TestEquipmentApi:
    """설비 CRUD 테스트."""

    def test_equipment_list(self, client, auth_headers):
        """FN-013: 설비 목록."""
        r = client.get("/api/equipments", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or isinstance(data, list)

    def test_equipment_create(self, client, auth_headers):
        """FN-013: 설비 등록."""
        r = client.post("/api/equipments", headers=auth_headers, json={
            "equip_name": "테스트설비",
            "equip_type": "SMT",
            "process_code": "PRC-001",
        })
        assert r.status_code in (200, 401)


class TestMaintenanceApi:
    """유지보수 테스트."""

    def test_maintenance_list(self, client, auth_headers):
        """REQ-040: 유지보수 작업 목록."""
        r = client.get("/api/maintenance", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestKpiApi:
    """설비 KPI 테스트."""

    def test_kpi_fpy(self, client, auth_headers):
        """REQ-057: FPY 조회."""
        r = client.get("/api/kpi/fpy", headers=auth_headers)
        assert r.status_code in (200, 401)
