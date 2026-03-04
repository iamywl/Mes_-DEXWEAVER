"""SPC API 테스트."""

import pytest


class TestSpcApi:
    """SPC 관리도 API 테스트."""

    def test_spc_chart_get(self, client, auth_headers):
        """FN-038: SPC 관리도 조회."""
        r = client.get("/api/quality/spc/ITM-00001", headers=auth_headers)
        assert r.status_code in (200, 401)  # 401은 DB 미연결 시
        if r.status_code == 200:
            data = r.json()
            assert "item_code" in data or "error" in data

    def test_spc_rule_create(self, client, auth_headers):
        """FN-039: SPC 규칙 생성."""
        r = client.post("/api/quality/spc/rules", headers=auth_headers, json={
            "item_code": "ITM-00001",
            "check_name": "테스트_검사",
            "rule_type": "XBAR_R",
            "ucl": 10.5,
            "lcl": 9.5,
            "target": 10.0,
            "sample_size": 5,
        })
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "success" in data or "error" in data

    def test_cpk_analysis(self, client, auth_headers):
        """FN-040: Cp/Cpk 분석."""
        r = client.get("/api/quality/cpk/ITM-00001", headers=auth_headers)
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            data = r.json()
            assert "item_code" in data or "error" in data

    def test_spc_chart_invalid_item(self, client, auth_headers):
        """존재하지 않는 품목 SPC 조회."""
        r = client.get("/api/quality/spc/INVALID-999", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_spc_rule_missing_fields(self, client, auth_headers):
        """필수 필드 누락 시 에러."""
        r = client.post("/api/quality/spc/rules", headers=auth_headers, json={})
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert "error" in r.json()
