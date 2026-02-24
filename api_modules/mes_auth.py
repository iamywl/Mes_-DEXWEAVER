"""FN-001~003: Authentication and authorization module."""

import os
import time

import bcrypt
import jwt

from api_modules.database import get_conn, release_conn


SECRET_KEY = os.getenv("JWT_SECRET", "mes-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def _hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _is_legacy_hash(hashed: str) -> bool:
    """Check if password uses old SHA-256 format (64 hex chars)."""
    return len(hashed) == 64 and all(c in '0123456789abcdef' for c in hashed)


def _verify_legacy_password(password: str, hashed: str) -> bool:
    """Verify against old SHA-256 hash for migration.

    Tries multiple legacy formats:
    1. SHA-256 with fixed salt prefix
    2. SHA-256 without salt (plain)
    """
    import hashlib
    # Try with salt
    salt = "mes-salt-fixed"
    if hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed:
        return True
    # Try without salt (some init scripts used plain SHA-256)
    if hashlib.sha256(password.encode()).hexdigest() == hashed:
        return True
    return False


def _create_token(user_id: str, role: str) -> str:
    """Create a standard JWT token using PyJWT."""
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_HOURS * 3600,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def _verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def login(user_id: str, password: str) -> dict:
    """FN-001: Login with user_id/password, return JWT token."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, role, password FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            cursor.close()
            return {"error": "Invalid user_id or password."}

        stored_hash = user[3]
        authenticated = False

        if _is_legacy_hash(stored_hash):
            # Legacy SHA-256 hash: verify and migrate to bcrypt
            if _verify_legacy_password(password, stored_hash):
                authenticated = True
                new_hash = _hash_password(password)
                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s",
                    (new_hash, user_id),
                )
                conn.commit()
        else:
            # bcrypt hash
            authenticated = _verify_password(password, stored_hash)

        if not authenticated:
            cursor.close()
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


async def update_permissions(user_id: str, data: dict) -> dict:
    """FN-003: Update user permissions."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            return {"error": "User not found."}

        perms = data.get("permissions", [])
        cursor.execute("DELETE FROM user_permissions WHERE user_id = %s", (user_id,))
        for p in perms:
            cursor.execute(
                "INSERT INTO user_permissions (user_id, menu, can_read, can_write) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, p["menu"], p.get("read", True), p.get("write", False)),
            )
        conn.commit()
        cursor.close()
        return {"success": True, "updated": len(perms)}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def list_users() -> dict:
    """List all users."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"users": []}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, email, role, created_at "
            "FROM users ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "users": [
                {
                    "user_id": r[0], "name": r[1], "email": r[2],
                    "role": r[3], "created_at": str(r[4]),
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
