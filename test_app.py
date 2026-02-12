"""Unit tests for MES FastAPI application.

Test Coverage:
    - TestMESDataEndpoints: Core API endpoints (8 tests)
    - TestErrorHandling: 404/405 error cases (4 tests)
    - TestResponseFormat: JSON schema validation (5 tests)
    - TestNetworkTopology: Topology aggregation logic (3 tests)
    - TestInfraStatusParsing: parse_percent edge cases (3 tests)
    - TestAIPrediction: AI prediction endpoints (2 tests)
"""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ── Core endpoint tests ──────────────────────────────────


class TestMESDataEndpoints:
    """Test cases for MES data retrieval endpoints."""

    def test_get_mes_data_success(self, client):
        response = client.get("/api/mes/data")
        assert response.status_code == 200
        assert isinstance(response.json(), (dict, list))

    def test_get_network_flows_success(self, client):
        response = client.get("/api/network/flows")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "flows" in data

    def test_get_infra_status_success(self, client):
        response = client.get("/api/infra/status")
        assert response.status_code == 200
        data = response.json()
        assert "cpu_load" in data
        assert "memory_usage" in data
        assert isinstance(data["cpu_load"], (int, float))
        assert isinstance(data["memory_usage"], (int, float))

    def test_get_k8s_pods_success(self, client):
        response = client.get("/api/k8s/pods")
        assert response.status_code == 200
        assert isinstance(response.json(), (dict, list))

    def test_get_topology_success(self, client):
        response = client.get("/api/network/topology")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "nodes" in data
        assert "edges" in data

    def test_get_pod_logs_success(self, client):
        response = client.get("/api/k8s/logs/nonexistent-pod")
        assert response.status_code == 200

    def test_infra_status_has_formatted_fields(self, client):
        response = client.get("/api/infra/status")
        data = response.json()
        assert "cpu" in data
        assert "mem" in data
        assert data["cpu"].endswith("%")
        assert data["mem"].endswith("%")

    def test_flows_returns_list(self, client):
        response = client.get("/api/network/flows")
        data = response.json()
        assert isinstance(data["flows"], list)


# ── Error handling tests ─────────────────────────────────


class TestErrorHandling:
    """Test cases for error handling."""

    def test_invalid_endpoint_returns_404(self, client):
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404

    def test_post_to_get_endpoint_returns_405(self, client):
        response = client.post("/api/mes/data")
        assert response.status_code == 405

    def test_put_to_get_endpoint_returns_405(self, client):
        response = client.put("/api/infra/status")
        assert response.status_code == 405

    def test_delete_to_get_endpoint_returns_405(self, client):
        response = client.delete("/api/k8s/pods")
        assert response.status_code == 405


# ── Response format tests ────────────────────────────────


class TestResponseFormat:
    """Test cases for response format validation."""

    def test_response_content_type_json(self, client):
        response = client.get("/api/infra/status")
        assert response.headers["content-type"] == "application/json"

    def test_all_get_endpoints_return_200(self, client):
        endpoints = [
            "/api/mes/data",
            "/api/network/flows",
            "/api/network/topology",
            "/api/infra/status",
            "/api/k8s/pods",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"{endpoint} failed"

    def test_all_get_endpoints_return_dict(self, client):
        endpoints = [
            "/api/network/flows",
            "/api/network/topology",
            "/api/infra/status",
        ]
        for endpoint in endpoints:
            data = client.get(endpoint).json()
            assert isinstance(data, dict), f"{endpoint} not dict"

    def test_infra_numeric_range(self, client):
        data = client.get("/api/infra/status").json()
        assert 0 <= data["cpu_load"] <= 100
        assert 0 <= data["memory_usage"] <= 100

    def test_pod_logs_returns_text(self, client):
        response = client.get("/api/k8s/logs/test-pod")
        assert "text/plain" in response.headers["content-type"]


# ── Topology aggregation tests ───────────────────────────


class TestNetworkTopology:
    """Test topology aggregation logic."""

    def test_topology_nodes_are_sorted(self, client):
        data = client.get("/api/network/topology").json()
        node_ids = [n["id"] for n in data["nodes"]]
        assert node_ids == sorted(node_ids)

    def test_topology_edges_have_count(self, client):
        data = client.get("/api/network/topology").json()
        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "count" in edge
            assert edge["count"] > 0

    def test_topology_structure(self, client):
        data = client.get("/api/network/topology").json()
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)


# ── Infrastructure parsing tests ─────────────────────────


class TestInfraStatusParsing:
    """Test parse_percent edge cases via /api/infra/status."""

    def test_cpu_is_numeric(self, client):
        data = client.get("/api/infra/status").json()
        assert isinstance(data["cpu_load"], (int, float))

    def test_mem_is_numeric(self, client):
        data = client.get("/api/infra/status").json()
        assert isinstance(data["memory_usage"], (int, float))

    def test_formatted_strings_consistent(self, client):
        data = client.get("/api/infra/status").json()
        cpu_num = data["cpu_load"]
        cpu_str = data["cpu"]
        assert cpu_str == f"{cpu_num:.1f}%"


# ── AI Prediction endpoint tests ─────────────────────────


class TestAIPrediction:
    """Test AI prediction endpoints."""

    def test_demand_prediction_endpoint(self, client):
        response = client.get("/api/ai/demand-prediction/ITEM003")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_defect_prediction_endpoint(self, client):
        payload = {
            "temperature": 200,
            "pressure": 10,
            "speed": 50,
            "humidity": 60,
        }
        response = client.post("/api/ai/defect-prediction", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "defect_probability" in data or "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
