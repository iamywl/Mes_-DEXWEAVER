"""Phase 2+/3/3+ 고급 기능 API 테스트."""

import pytest


class TestMsaApi:
    """MSA/Gage R&R 테스트 (REQ-059)."""

    def test_msa_studies(self, client, auth_headers):
        r = client.get("/api/quality/msa/studies", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_msa_create(self, client, auth_headers):
        r = client.post("/api/quality/msa/studies", headers=auth_headers, json={
            "study_name": "테스트 GRR",
            "gauge_name": "마이크로미터",
            "part_number": "PART-001",
            "characteristic": "두께",
            "num_operators": 3,
            "num_parts": 10,
            "num_trials": 3,
            "tolerance": 0.05,
        })
        assert r.status_code in (200, 401)


class TestFmeaApi:
    """FMEA 테스트 (REQ-061)."""

    def test_fmea_list(self, client, auth_headers):
        r = client.get("/api/quality/fmea", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestEnergyApi:
    """에너지 관리 테스트 (REQ-063)."""

    def test_energy_dashboard(self, client, auth_headers):
        r = client.get("/api/energy/dashboard", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestCalibrationApi:
    """교정 관리 테스트 (REQ-064)."""

    def test_calibration_gauges(self, client, auth_headers):
        r = client.get("/api/calibration/gauges", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestSupplierApi:
    """공급업체 품질 테스트 (REQ-065)."""

    def test_supplier_list(self, client, auth_headers):
        r = client.get("/api/suppliers", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestBatchApi:
    """배치 실행 테스트 (REQ-071)."""

    def test_batch_list(self, client, auth_headers):
        r = client.get("/api/batch/orders", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_batch_create(self, client, auth_headers):
        r = client.post("/api/batch/orders", headers=auth_headers, json={
            "item_code": "CHEM-001",
            "batch_size": 500,
        })
        assert r.status_code in (200, 401)


class TestEcmApi:
    """설계변경관리 테스트 (REQ-073)."""

    def test_ecr_list(self, client, auth_headers):
        r = client.get("/api/ecm/ecr", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestMultisiteApi:
    """멀티사이트 테스트 (REQ-075)."""

    def test_sites_list(self, client, auth_headers):
        r = client.get("/api/sites", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_site_dashboard(self, client, auth_headers):
        r = client.get("/api/sites/1/dashboard", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestReportApi:
    """리포트 빌더 테스트 (REQ-070)."""

    def test_report_templates(self, client, auth_headers):
        r = client.get("/api/reports/templates", headers=auth_headers)
        assert r.status_code in (200, 401)


class TestRoutingApi:
    """복합라우팅 테스트 (REQ-074)."""

    def test_routing_list(self, client, auth_headers):
        r = client.get("/api/routings/complex", headers=auth_headers)
        assert r.status_code in (200, 401)
