"""NFR-004: Shared auth dependencies for APIRouter modules."""

from fastapi import HTTPException, Request
from api_modules import mes_auth


async def auth_required(request: Request):
    """Depends — 인증 필수. dict 에러 시 HTTPException 변환."""
    result = await mes_auth.require_auth(request)
    if isinstance(result, dict) and "error" in result:
        status = result.pop("_status", 401)
        raise HTTPException(status_code=status, detail=result["error"])
    return result


async def admin_required(request: Request):
    """Depends — 관리자 전용."""
    result = await mes_auth.require_admin(request)
    if isinstance(result, dict) and "error" in result:
        status = result.pop("_status", 403)
        raise HTTPException(status_code=status, detail=result["error"])
    return result
