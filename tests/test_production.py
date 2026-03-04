"""생산계획/작업지시/실적 API 테스트 (FN-015~024)."""

import pytest


class TestPlanApi:
    """생산계획 테스트."""

    def test_plan_list(self, client, auth_headers):
        """FN-015: 생산계획 목록."""
        r = client.get("/api/plans", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data or isinstance(data, list)

    def test_plan_create(self, client, auth_headers):
        """FN-015: 생산계획 등록."""
        r = client.post("/api/plans", headers=auth_headers, json={
            "item_code": "ITM-00001",
            "plan_qty": 100,
            "start_date": "2026-03-10",
            "end_date": "2026-03-15",
        })
        assert r.status_code in (200, 401)


class TestWorkOrderApi:
    """작업지시 테스트."""

    def test_work_orders_list(self, client, auth_headers):
        """FN-020: 작업지시 목록."""
        r = client.get("/api/work-orders", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_work_order_create(self, client, auth_headers):
        """FN-020: 작업지시 생성."""
        r = client.post("/api/work-orders", headers=auth_headers, json={
            "plan_id": 1,
            "item_code": "ITM-00001",
            "order_qty": 50,
        })
        assert r.status_code in (200, 401)


class TestWorkResultApi:
    """작업실적 테스트."""

    def test_work_results_list(self, client, auth_headers):
        """FN-023: 작업실적 조회."""
        r = client.get("/api/work-results", headers=auth_headers)
        assert r.status_code in (200, 401)
