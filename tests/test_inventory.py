"""재고관리 API 테스트 (FN-029~031)."""

import pytest


class TestInventoryApi:
    """재고 CRUD 테스트."""

    def test_inventory_list(self, client, auth_headers):
        """FN-031: 재고현황."""
        r = client.get("/api/inventory", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or isinstance(data, list)

    def test_inventory_in(self, client, auth_headers):
        """FN-029: 입고."""
        r = client.post("/api/inventory/in", headers=auth_headers, json={
            "item_code": "ITM-00001",
            "qty": 100,
            "lot_no": "LOT-TEST-001",
        })
        assert r.status_code in (200, 401)

    def test_inventory_out(self, client, auth_headers):
        """FN-030: 출고."""
        r = client.post("/api/inventory/out", headers=auth_headers, json={
            "item_code": "ITM-00001",
            "qty": 10,
        })
        assert r.status_code in (200, 401)
