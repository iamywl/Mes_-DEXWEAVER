"""pytest fixtures — DB 연결, 인증 토큰, FastAPI 테스트 클라이언트."""

import os
import pytest
from fastapi.testclient import TestClient

# DB를 테스트용으로 전환 (import 전에 설정)
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:mes1234@localhost:5432/mes_db")

from app import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_token(client):
    """admin 사용자의 JWT 토큰."""
    r = client.post("/api/auth/login", json={"user_id": "admin", "password": "admin123"})
    if r.status_code == 200 and "token" in r.json():
        return r.json()["token"]
    # 토큰 획득 실패 시 더미 토큰 (DB 미연결 상태)
    return "test-token"


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """인증 헤더."""
    return {"Authorization": f"Bearer {auth_token}"}
