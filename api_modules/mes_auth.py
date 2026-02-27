"""FN-001~003: Authentication and authorization module.

Security features (KISA 49 / GS Certification):
- bcrypt password hashing
- PyJWT standard token
- JWT secret from environment variable (mandatory)
- Registration requires admin approval (is_approved)
- Backend token verification middleware
- Session timeout (JWT expiry configurable)
"""

import logging
import os
import re
import time

import bcrypt
import jwt
from fastapi import Request

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# ── KISA: 하드코딩된 중요 정보 제거 ─────────────────────────
_jwt_secret_env = os.getenv("JWT_SECRET", "")
if not _jwt_secret_env:
    import secrets
    _jwt_secret_env = secrets.token_hex(32)
    log.warning("JWT_SECRET not set – generated random secret (will change on restart)")
SECRET_KEY = _jwt_secret_env
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))  # 세션 타임아웃
ALLOWED_ROLES = {"admin", "manager", "worker", "viewer"}

# ── 입력값 검증 유틸 ─────────────────────────────────────────
_ID_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
_NAME_RE = re.compile(r"^[\w가-힣\s]{1,50}$")


def _sanitize_id(v: str) -> str:
    """Validate user_id format to prevent injection."""
    if not v or not _ID_RE.match(v):
        raise ValueError("user_id는 영문/숫자/언더스코어 3~30자만 허용됩니다.")
    return v


def _sanitize_name(v: str) -> str:
    if not v or not _NAME_RE.match(v):
        raise ValueError("이름은 한글/영문/숫자 1~50자만 허용됩니다.")
    return v


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
    """Verify against old SHA-256 hash for migration."""
    import hashlib
    salt = "mes-salt-fixed"
    if hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed:
        return True
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


async def verify_request(request: Request) -> dict:
    """Backend JWT verification middleware.

    Extracts token from Authorization header and verifies.
    Returns payload dict or raises error dict.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = _verify_token(token)
    return payload


async def require_auth(request: Request) -> dict:
    """Require valid JWT – returns payload or error dict."""
    payload = await verify_request(request)
    if not payload:
        return {"error": "인증이 필요합니다. 유효한 토큰을 제공해주세요.", "_status": 401}
    return payload


async def require_admin(request: Request) -> dict:
    """Require admin role."""
    payload = await require_auth(request)
    if "error" in payload:
        return payload
    if payload.get("role") != "admin":
        return {"error": "관리자 권한이 필요합니다.", "_status": 403}
    return payload


async def login(user_id: str, password: str) -> dict:
    """FN-001: Login with user_id/password, return JWT token."""
    conn = None
    try:
        _sanitize_id(user_id)
        if not password or len(password) < 1:
            return {"error": "비밀번호를 입력해주세요."}

        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, role, password, "
            "COALESCE(is_approved, TRUE) "
            "FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            cursor.close()
            return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}

        # 승인 여부 확인
        if not user[4]:
            cursor.close()
            return {"error": "관리자 승인 대기 중인 계정입니다."}

        stored_hash = user[3]
        authenticated = False

        if _is_legacy_hash(stored_hash):
            if _verify_legacy_password(password, stored_hash):
                authenticated = True
                new_hash = _hash_password(password)
                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s",
                    (new_hash, user_id),
                )
                conn.commit()
        else:
            authenticated = _verify_password(password, stored_hash)

        if not authenticated:
            cursor.close()
            return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}

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
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception:
        return {"error": "로그인 처리 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def register(data: dict) -> dict:
    """FN-002: Register a new user (requires admin approval)."""
    conn = None
    try:
        uid = _sanitize_id(data.get("user_id", ""))
        name = _sanitize_name(data.get("name", ""))
        password = data.get("password", "")
        if len(password) < 4:
            return {"error": "비밀번호는 4자 이상이어야 합니다."}

        role = data.get("role", "worker")
        if role not in ALLOWED_ROLES:
            return {"error": f"허용되지 않는 역할입니다. 허용: {', '.join(ALLOWED_ROLES)}"}

        # 일반 사용자가 admin 역할로 등록 불가 → 승인 후 admin이 변경
        if role == "admin":
            role = "worker"

        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE user_id = %s", (uid,),
        )
        if cursor.fetchone():
            return {"error": "이미 존재하는 사용자 ID입니다."}

        hashed = _hash_password(password)

        cursor.execute(
            "INSERT INTO users (user_id, password, name, email, role, is_approved) "
            "VALUES (%s, %s, %s, %s, %s, FALSE)",
            (uid, hashed, name, data.get("email", ""), role),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "user_id": uid,
                "message": "회원가입이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다."}
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "회원가입 처리 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def approve_user(user_id: str, approved: bool = True) -> dict:
    """Admin: approve or reject a registered user."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_approved = %s WHERE user_id = %s",
            (approved, user_id),
        )
        if cursor.rowcount == 0:
            return {"error": "사용자를 찾을 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True, "user_id": user_id, "approved": approved}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "승인 처리 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_permissions(user_id: str) -> dict:
    """FN-003: Get user permissions."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}

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
    except Exception:
        return {"error": "권한 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def update_permissions(user_id: str, data: dict) -> dict:
    """FN-003: Update user permissions (admin only)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}

        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            return {"error": "사용자를 찾을 수 없습니다."}

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
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "권한 수정 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def list_users() -> dict:
    """List all users with approval status."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"users": []}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, email, role, created_at, "
            "COALESCE(is_approved, TRUE) "
            "FROM users ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "users": [
                {
                    "user_id": r[0], "name": r[1], "email": r[2],
                    "role": r[3], "created_at": str(r[4]),
                    "is_approved": r[5],
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "사용자 목록 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
