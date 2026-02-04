import pytest
from fastapi.testclient import TestClient
from app import app, db_config
import psycopg2

# Use a fixture to override the db_config for testing
@pytest.fixture(name="mock_db_config")
def mock_db_config_fixture(monkeypatch):
    test_db_config = {
        "host": "localhost",  # Or a test-specific host
        "database": "test_mes_db",
        "user": "test_user",
        "password": "test_password",
        "connect_timeout": 1
    }
    monkeypatch.setattr("app.db_config", test_db_config)
    return test_db_config

@pytest.fixture(name="mock_conn_cursor")
def mock_conn_cursor_fixture(monkeypatch):
    class MockCursor:
        def __init__(self, cursor_factory=None):
            self.data = {
                'items': [{'id': 1, 'name': 'Item A'}],
                'production_plans': [{'id': 1, 'product_id': 101}],
                'processes': [{'id': 1, 'name': 'Process X'}],
                'equipments': [{'id': 1, 'name': 'Equipment Y'}],
            }
            self.current_table = None

        def execute(self, query):
            if "FROM items" in query:
                self.current_table = 'items'
            elif "FROM production_plans" in query:
                self.current_table = 'production_plans'
            elif "FROM processes" in query:
                self.current_table = 'processes'
            elif "FROM equipments" in query:
                self.current_table = 'equipments'
            else:
                self.current_table = None

        def fetchall(self):
            return self.data.get(self.current_table, [])

        def close(self):
            pass

    class MockConnection:
        def cursor(self, cursor_factory=None):
            return MockCursor(cursor_factory)

        def close(self):
            pass

    monkeypatch.setattr(psycopg2, "connect", lambda **kwargs: MockConnection())


def test_get_mes_data_success(mock_db_config, mock_conn_cursor):
    client = TestClient(app)
    response = client.get("/api/data")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "production_plans" in response.json()
    assert "processes" in response.json()
    assert "equipments" in response.json()
    assert response.json()["items"][0]["name"] == "Item A"


def test_get_mes_data_db_error(mock_db_config, monkeypatch):
    def mock_psycopg2_connect_error(*args, **kwargs):
        raise psycopg2.OperationalError("Test connection error")

    monkeypatch.setattr(psycopg2, "connect", mock_psycopg2_connect_error)
    client = TestClient(app)
    response = client.get("/api/data")
    assert response.status_code == 200  # FastAPI returns 200 even for errors caught in the endpoint
    assert "error" in response.json()
    assert "Test connection error" in response.json()["error"]