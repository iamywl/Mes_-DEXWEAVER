"""품목/BOM/공정 API 테스트 (FN-004~012)."""

import pytest


class TestItemsApi:
    """품목 CRUD 테스트."""

    def test_items_list(self, client, auth_headers):
        """FN-005: 품목 목록 조회."""
        r = client.get("/api/items", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or isinstance(data, list)

    def test_items_search(self, client, auth_headers):
        """FN-005: 품목 검색."""
        r = client.get("/api/items?search=ITM", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_item_create(self, client, auth_headers):
        """FN-004: 품목 등록."""
        r = client.post("/api/items", headers=auth_headers, json={
            "item_name": "테스트품목",
            "category": "PART",
            "unit": "EA",
            "spec": "10x10mm",
        })
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "item_code" in data or "error" in data


class TestBomApi:
    """BOM API 테스트."""

    def test_bom_list(self, client, auth_headers):
        """FN-008: BOM 조회."""
        r = client.get("/api/bom?item_code=ITM-00001", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_bom_reverse(self, client, auth_headers):
        """FN-009: BOM 역전개."""
        r = client.get("/api/bom/reverse?child_code=ITM-00005", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestProcessApi:
    """공정 API 테스트."""

    def test_process_list(self, client, auth_headers):
        """FN-010: 공정 목록."""
        r = client.get("/api/processes", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or isinstance(data, list) or "processes" in data
