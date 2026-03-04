"""품질관리 API 테스트 (FN-025~028, 검사/불량/CAPA)."""

import pytest


class TestInspectionApi:
    """품질검사 테스트."""

    def test_inspection_list(self, client, auth_headers):
        """FN-025: 검사 목록."""
        r = client.get("/api/inspections", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or isinstance(data, list)

    def test_inspection_create(self, client, auth_headers):
        """FN-025: 검사 등록."""
        r = client.post("/api/inspections", headers=auth_headers, json={
            "item_code": "ITM-00001",
            "process_code": "PRC-001",
            "result": "PASS",
            "inspector": "inspector1",
        })
        assert r.status_code in (200, 401)


class TestNcrApi:
    """부적합품(NCR) 테스트."""

    def test_ncr_list(self, client, auth_headers):
        """REQ-054: NCR 목록."""
        r = client.get("/api/quality/ncr", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_ncr_create(self, client, auth_headers):
        """REQ-054: NCR 등록."""
        r = client.post("/api/quality/ncr", headers=auth_headers, json={
            "item_code": "ITM-00001",
            "lot_no": "LOT-20260301-001",
            "defect_type": "DIMENSION",
            "defect_qty": 5,
            "description": "치수 불량",
        })
        assert r.status_code in (200, 401)


class TestDispositionApi:
    """출하판정 테스트."""

    def test_disposition_list(self, client, auth_headers):
        """REQ-056: 출하판정 목록."""
        r = client.get("/api/quality/disposition", headers=auth_headers)
        assert r.status_code in (200, 401)
