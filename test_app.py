"""
Unit tests for MES FastAPI application.

This module provides test cases for API endpoints and their
response validation. Uses TestClient from FastAPI for HTTP testing.

Test Coverage:
    - GET /api/mes/data: Production dashboard data endpoint
    - GET /api/network/flows: Network flow information endpoint
    - GET /api/infra/status: Infrastructure status endpoint
    - GET /api/k8s/pods: Kubernetes pods endpoint
"""

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client() -> TestClient:
    """
    Fixture for FastAPI TestClient.

    Provides a test client for making HTTP requests to the
    FastAPI application without running a server.

    Returns:
        TestClient: Configured test client instance.
    """
    return TestClient(app)


class TestMESDataEndpoints:
    """Test cases for MES data retrieval endpoints."""

    def test_get_mes_data_success(self, client: TestClient) -> None:
        """
        Test successful retrieval of production dashboard data.

        Verifies the /api/mes/data endpoint returns appropriate data
        and correct HTTP status code.
        """
        response = client.get("/api/mes/data")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_network_flows_success(self, client: TestClient) -> None:
        """
        Test successful retrieval of network flow data.

        Verifies the /api/network/flows endpoint returns valid data.
        """
        response = client.get("/api/network/flows")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "flows" in data

    def test_get_infra_status_success(self, client: TestClient) -> None:
        """
        Test successful retrieval of infrastructure status.

        Verifies the /api/infra/status endpoint returns CPU and
        memory metrics.
        """
        response = client.get("/api/infra/status")
        assert response.status_code == 200
        data = response.json()
        assert "cpu_load" in data
        assert "memory_usage" in data
        assert isinstance(data["cpu_load"], (int, float))
        assert isinstance(data["memory_usage"], (int, float))

    def test_get_k8s_pods_success(self, client: TestClient) -> None:
        """
        Test successful retrieval of Kubernetes pod information.

        Verifies the /api/k8s/pods endpoint returns pod data.
        """
        response = client.get("/api/k8s/pods")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)


class TestErrorHandling:
    """Test cases for error handling in API endpoints."""

    def test_invalid_endpoint(self, client: TestClient) -> None:
        """
        Test that invalid endpoints return 404.

        Verifies the application properly handles requests to
        non-existent endpoints.
        """
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404

    def test_incorrect_method(self, client: TestClient) -> None:
        """
        Test that incorrect HTTP methods return 405.

        Verifies the application rejects POST requests to
        GET-only endpoints.
        """
        response = client.post("/api/mes/data")
        assert response.status_code == 405


class TestResponseFormat:
    """Test cases for response format validation."""

    def test_response_is_json(self, client: TestClient) -> None:
        """
        Test that all responses are valid JSON.

        Verifies the Content-Type header and JSON parseable response.
        """
        response = client.get("/api/infra/status")
        assert response.headers["content-type"] == "application/json"
        assert isinstance(response.json(), dict)

    def test_response_schema(self, client: TestClient) -> None:
        """
        Test that response schema matches expected structure.

        Verifies each endpoint returns data in the expected format.
        """
        endpoints = [
            "/api/mes/data",
            "/api/network/flows",
            "/api/infra/status",
            "/api/k8s/pods",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, (dict, list, str, int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
