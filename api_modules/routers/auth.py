"""Auth router — FN-001~003: login/register/permissions."""

from fastapi import APIRouter, Depends, Request

from api_modules import mes_auth, security
from api_modules.auth_deps import auth_required, admin_required
from api_modules.rate_limit import limiter

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    body = await request.json()
    uid = body.get("user_id", "")
    pw = body.get("password", "")
    if not uid or not pw:
        return {"error": "아이디와 비밀번호를 입력해주세요."}
    lock_msg = security.check_login_lock(uid)
    if lock_msg:
        security.log_security_event("LOGIN_BLOCKED", lock_msg, user_id=uid,
                                    ip=request.client.host if request.client else None)
        return {"error": lock_msg}
    result = await mes_auth.login(uid, pw)
    ip = request.client.host if request.client else None
    if isinstance(result, dict) and "error" in result:
        security.record_login_failure(uid)
        security.log_security_event("LOGIN_FAIL", result["error"], user_id=uid, ip=ip)
    else:
        security.record_login_success(uid)
        security.log_security_event("LOGIN_OK", "로그인 성공", user_id=uid, ip=ip)
    return result


@router.post("/register")
async def register(request: Request):
    return await mes_auth.register(await request.json())


@router.get("/permissions/{user_id}")
async def get_permissions(user_id: str, request: Request,
                          user=Depends(auth_required)):
    return await mes_auth.get_permissions(user_id)


@router.put("/permissions/{user_id}")
async def update_permissions(user_id: str, request: Request,
                             user=Depends(admin_required)):
    return await mes_auth.update_permissions(user_id, await request.json())


@router.get("/users")
async def list_users(request: Request, user=Depends(auth_required)):
    return await mes_auth.list_users()


@router.put("/approve/{user_id}")
async def approve_user(user_id: str, request: Request,
                       user=Depends(admin_required)):
    body = await request.json()
    return await mes_auth.approve_user(user_id, body.get("approved", True))
