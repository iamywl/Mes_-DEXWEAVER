"""LOT 추적 API 테스트."""

import pytest


class TestLotTraceApi:
    """LOT 계보 추적 API 테스트."""

    def test_lot_genealogy(self, client, auth_headers):
        """FN-048: LOT 계보 추적 (Forward/Backward)."""
        r = client.get("/api/lot/genealogy/LOT-20260301-001", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "lot_no" in data or "error" in data

    def test_lot_genealogy_forward(self, client, auth_headers):
        """Forward 방향만 추적."""
        r = client.get("/api/lot/genealogy/LOT-20260301-001?direction=forward",
                       headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_lot_genealogy_backward(self, client, auth_headers):
        """Backward 방향만 추적."""
        r = client.get("/api/lot/genealogy/LOT-20260301-001?direction=backward",
                       headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_lot_genealogy_invalid(self, client, auth_headers):
        """존재하지 않는 LOT 추적."""
        r = client.get("/api/lot/genealogy/INVALID-LOT-999", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert "error" in r.json()
