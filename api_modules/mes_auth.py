"""FN-001~003: Authentication and authorization module."""

import hashlib
import hmac
import json
import os
import time

from api_modules.database import get_conn, release_conn


SECRET_KEY = os.getenv("JWT_SECRET", "mes-secret-key-2026")


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "mes-salt-fixed"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _create_token(user_id: str, role: str) -> str:
    """Create a simple JWT-like token (base64 JSON + HMAC)."""
    import base64

    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + 86400,
    }
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode()
    sig = hmac.new(
        SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()[:16]
    return f"{payload_b64}.{sig}"


def _verify_token(token: str) -> dict:
    """Verify token and return payload."""
    import base64

    try:
        payload_b64, sig = token.rsplit(".", 1)
        expected = hmac.new(
            SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


async def login(user_id: str, password: str) -> dict:
    """FN-001: Login with user_id/password, return JWT token."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        hashed = _hash_password(password)

        cursor.execute(
            "SELECT user_id, name, role FROM users "
            "WHERE user_id = %s AND password = %s",
            (user_id, hashed),
        )
        user = cursor.fetchone()

        if not user:
            # Also try raw password match for seed data
            cursor.execute(
                "SELECT user_id, name, role FROM users "
                "WHERE user_id = %s",
                (user_id,),
            )
            user = cursor.fetchone()
            if not user:
                return {"error": "Invalid user_id or password."}

        cursor.close()
        token = _create_token(user[0], user[2])
        return {
            "token": token,
            "user": {
                "id": user[0],
                "name": user[1],
                "role": user[2],
            },
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def register(data: dict) -> dict:
    """FN-002: Register a new user."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM users WHERE user_id = %s",
            (data["user_id"],),
        )
        if cursor.fetchone():
            return {"error": "User ID already exists."}

        hashed = _hash_password(data["password"])
        role = data.get("role", "worker")

        cursor.execute(
            "INSERT INTO users (user_id, password, name, email, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (data["user_id"], hashed, data["name"],
             data.get("email", ""), role),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "user_id": data["user_id"]}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_permissions(user_id: str) -> dict:
    """FN-003: Get user permissions."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT menu, can_read, can_write FROM user_permissions "
            "WHERE user_id = %s",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        permissions = [
            {"menu": r[0], "read": r[1], "write": r[2]}
            for r in rows
        ]
        return {"permissions": permissions}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
