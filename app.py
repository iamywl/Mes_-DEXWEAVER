"""MES Backend Application — NFR-010: APIRouter-based modular architecture.

FastAPI-based Manufacturing Execution System API server.
Full FN-001 ~ FN-066 + REQ-052~075 implementation.

GS Certification compliance:
- KISA 49: Backend JWT auth, input validation, error handling
- KS X 9003: MES functional completeness
- ISO/IEC 25051: Document-code consistency
"""

import os
import logging
import traceback

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import uvicorn

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api_modules import mes_auth, mes_notification
from api_modules.rate_limit import limiter
from api_modules.routers import all_routers

# Prometheus metrics (graceful fallback)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False

log = logging.getLogger(__name__)

# ── Rate Limiter (NFR-007) — shared instance from rate_limit.py ──

app = FastAPI(title="DEXWEAVER MES API", version="6.0",
              docs_url="/api/docs", redoc_url="/api/redoc")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_env = os.getenv("CORS_ORIGINS", "")
_allowed_origins = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env
    else ["http://localhost:30173", "http://localhost:3000"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── Prometheus Metrics Instrumentation ──
if _HAS_PROMETHEUS:
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/api/health", "/api/docs", "/api/redoc"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# ── NFR-018: API Versioning Middleware (/api/v1/* → /api/*) ──
@app.middleware("http")
async def api_version_rewrite(request: Request, call_next):
    """Support /api/v1/ prefix — rewrite to /api/ for backward compatibility."""
    path = request.scope.get("path", "")
    if path.startswith("/api/v1/"):
        request.scope["path"] = "/api/" + path[8:]
    return await call_next(request)


# ── KISA: Global Exception Handler (Stack Trace 노출 방지) ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "서버 내부 오류가 발생했습니다. 관리자에게 문의해주세요."},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "요청한 리소스를 찾을 수 없습니다."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"error": exc.detail})


# ── NFR-010: Register all domain routers ──
for router in all_routers:
    app.include_router(router)


# ── WebSocket (not in router — needs top-level /ws path) ──
@app.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    user_payload = await mes_auth.verify_token(token) if token else None
    user_id = (user_payload.get("user_id", "anonymous")
               if isinstance(user_payload, dict) else "anonymous")

    await mes_notification.manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        mes_notification.manager.disconnect(websocket, user_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
