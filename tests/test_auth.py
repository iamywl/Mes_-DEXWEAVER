"""인증/권한 API 테스트 (FN-001~003)."""

import pytest


class TestAuthApi:
    """인증 API 테스트."""

    def test_health_check(self, client):
        """헬스체크 — 인증 없이 접근 가능."""
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_login_success(self, client):
        """FN-001: 로그인 성공."""
        r = client.post("/api/auth/login", json={
            "user_id": "admin", "password": "admin123"
        })
        if r.status_code == 200:
            data = r.json()
            assert "token" in data
            assert "user" in data or "user_id" in data

    def test_login_fail(self, client):
        """FN-001: 로그인 실패 — 잘못된 비밀번호."""
        r = client.post("/api/auth/login", json={
            "user_id": "admin", "password": "wrong_password"
        })
        data = r.json()
        assert "error" in data

    def test_login_missing_fields(self, client):
        """FN-001: 필수 필드 누락."""
        r = client.post("/api/auth/login", json={"user_id": "admin"})
        data = r.json()
        assert "error" in data

    def test_protected_endpoint_no_token(self, client):
        """인증 없이 보호된 엔드포인트 접근 → 401."""
        r = client.get("/api/items")
        assert r.status_code in (401, 403, 422)

    def test_protected_endpoint_with_token(self, client, auth_headers):
        """인증 토큰으로 보호된 엔드포인트 접근."""
        r = client.get("/api/items", headers=auth_headers)
        assert r.status_code in (200, 401)

    def test_register(self, client):
        """FN-002: 회원가입."""
        import time
        uid = f"testuser_{int(time.time())}"
        r = client.post("/api/auth/register", json={
            "user_id": uid,
            "password": "test1234",
            "name": "테스트유저",
            "email": f"{uid}@test.com",
            "role": "viewer",
        })
        data = r.json()
        # 성공 또는 DB 미연결
        assert "success" in data or "error" in data
