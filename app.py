"""MES Backend Application.

FastAPI-based Manufacturing Execution System API server.
Full FN-001 ~ FN-038 implementation.

GS Certification compliance:
- KISA 49: Backend JWT auth, input validation, error handling
- KS X 9003: MES functional completeness
- ISO/IEC 25051: Document-code consistency
"""

import os
import logging
import traceback

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

from fastapi import WebSocket, WebSocketDisconnect

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api_modules import (
    k8s_service,
    mes_ai_prediction,
    mes_auth,
    mes_bom,
    mes_capa,
    mes_dashboard,
    mes_defect_predict,
    mes_equipment,
    mes_inventory,
    mes_inventory_movement,
    mes_inventory_status,
    mes_items,
    mes_lot_trace,
    mes_notification,
    mes_oee,
    mes_plan,
    mes_process,
    mes_quality,
    mes_reports,
    mes_spc,
    mes_work,
    sys_logic,
)
from api_modules import security
from api_modules import mes_barcode
from api_modules import mes_ewi
from api_modules import mes_ncr
from api_modules import mes_disposition
from api_modules import mes_kpi
from api_modules import mes_maintenance
from api_modules import mes_recipe
from api_modules import mes_datacollect
from api_modules import mes_document
from api_modules import mes_labor
from api_modules import mes_erp
from api_modules import mes_opcua
from api_modules import mes_i18n
from api_modules import mes_audit
from api_modules import mes_resource
from api_modules import mes_msa
from api_modules import mes_fmea
from api_modules import mes_energy
from api_modules import mes_calibration
from api_modules import mes_sqm
from api_modules import mes_dispatch
from api_modules import mes_setup
from api_modules import mes_costing
from api_modules import mes_dashboard_builder
from api_modules import mes_report_builder
from api_modules import mes_batch
from api_modules import mes_ecm
from api_modules import mes_complex_routing
from api_modules import mes_multisite

# Prometheus metrics (graceful fallback)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False

log = logging.getLogger(__name__)

# ── Rate Limiter (NFR-007) ────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

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


# ── Auth Dependencies (Depends 기반) ─────────────────────────
async def auth_required(request: Request):
    """기존 require_auth 래핑 — dict 에러 반환 시 HTTPException으로 변환."""
    result = await mes_auth.require_auth(request)
    if isinstance(result, dict) and "error" in result:
        status = result.pop("_status", 401)
        raise HTTPException(status_code=status, detail=result["error"])
    return result


async def admin_required(request: Request):
    """기존 require_admin 래핑."""
    result = await mes_auth.require_admin(request)
    if isinstance(result, dict) and "error" in result:
        status = result.pop("_status", 403)
        raise HTTPException(status_code=status, detail=result["error"])
    return result


# ── FN-001~003: Auth (public endpoints) ─────────────────────

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    body = await request.json()
    uid = body.get("user_id", "")
    pw = body.get("password", "")
    if not uid or not pw:
        return {"error": "아이디와 비밀번호를 입력해주세요."}
    # NFR-012: 로그인 잠금 확인
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


@app.post("/api/auth/register")
async def register(request: Request):
    return await mes_auth.register(await request.json())


@app.get("/api/auth/permissions/{user_id}")
async def get_permissions(user_id: str, request: Request,
                          user=Depends(auth_required)):
    return await mes_auth.get_permissions(user_id)


@app.put("/api/auth/permissions/{user_id}")
async def update_permissions(user_id: str, request: Request,
                             user=Depends(admin_required)):
    return await mes_auth.update_permissions(user_id, await request.json())


@app.get("/api/auth/users")
async def list_users(request: Request, user=Depends(auth_required)):
    return await mes_auth.list_users()


@app.put("/api/auth/approve/{user_id}")
async def approve_user(user_id: str, request: Request,
                       user=Depends(admin_required)):
    body = await request.json()
    return await mes_auth.approve_user(user_id, body.get("approved", True))


# ── FN-004~007: Items ────────────────────────────────────────

@app.post("/api/items")
async def create_item(request: Request, user=Depends(auth_required)):
    return await mes_items.create_item(await request.json())


@app.get("/api/items")
async def list_items(keyword: str = None, category: str = None,
                     page: int = 1, size: int = 20, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_items.get_items(keyword, category, page, size)


@app.get("/api/items/{item_code}")
async def get_item(item_code: str, request: Request,
                   user=Depends(auth_required)):
    return await mes_items.get_item_detail(item_code)


@app.put("/api/items/{item_code}")
async def update_item(item_code: str, request: Request,
                      user=Depends(auth_required)):
    return await mes_items.update_item(item_code, await request.json())


@app.delete("/api/items/{item_code}")
async def delete_item(item_code: str, request: Request,
                      user=Depends(auth_required)):
    return await mes_items.delete_item(item_code)


# ── FN-008~009: BOM ──────────────────────────────────────────

@app.post("/api/bom")
async def create_bom(request: Request, user=Depends(auth_required)):
    return await mes_bom.create_bom(await request.json())


@app.get("/api/bom")
async def list_bom(request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.list_bom()


@app.put("/api/bom/{bom_id}")
async def update_bom(bom_id: int, request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.update_bom(bom_id, await request.json())


@app.delete("/api/bom/{bom_id}")
async def delete_bom(bom_id: int, request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.delete_bom(bom_id)


@app.get("/api/bom/summary")
async def bom_summary(request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.bom_summary()


@app.get("/api/bom/where-used/{item_code}")
async def bom_where_used(item_code: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.where_used(item_code)


@app.get("/api/bom/explode/{item_code}")
async def explode_bom(item_code: str, qty: float = 1, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_bom.explode_bom(item_code, qty)


# ── FN-010~012: Process & Routing ────────────────────────────

@app.get("/api/processes")
async def list_processes(request: Request,
                     user=Depends(auth_required)):
    return await mes_process.list_processes()


@app.post("/api/processes")
async def create_process(request: Request,
                     user=Depends(auth_required)):
    return await mes_process.create_process(await request.json())


@app.put("/api/processes/{process_code}")
async def update_process(process_code: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_process.update_process(process_code, await request.json())


@app.delete("/api/processes/{process_code}")
async def delete_process(process_code: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_process.delete_process(process_code)


@app.get("/api/routings")
async def list_routings_summary(request: Request,
                     user=Depends(auth_required)):
    return await mes_process.list_routings_summary()


@app.post("/api/routings")
async def create_routing(request: Request,
                     user=Depends(auth_required)):
    return await mes_process.create_routing(await request.json())


@app.get("/api/routings/{item_code}")
async def get_routing(item_code: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_process.get_routing(item_code)


# ── FN-013~014: Equipment ────────────────────────────────────

@app.post("/api/equipments")
async def create_equipment(request: Request,
                     user=Depends(auth_required)):
    return await mes_equipment.create_equipment(await request.json())


@app.get("/api/equipments")
async def list_equipments(process_code: str = None, status: str = None,
                          request: Request = None,
                     user=Depends(auth_required)):
    return await mes_equipment.get_equipments(process_code, status)


# ── FN-015~017: Plans ────────────────────────────────────────

@app.post("/api/plans")
async def create_plan(request: Request,
                     user=Depends(auth_required)):
    return await mes_plan.create_plan(await request.json())


@app.get("/api/plans")
async def list_plans(start_date: str = None, end_date: str = None,
                     status: str = None, page: int = 1, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_plan.get_plans(start_date, end_date, status, page)


@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: int, request: Request,
                     user=Depends(auth_required)):
    return await mes_plan.get_plan_detail(plan_id)


# ── FN-018~019: AI Planning ──────────────────────────────────

@app.post("/api/ai/demand-forecast")
async def demand_forecast(request: Request,
                     user=Depends(auth_required)):
    body = await request.json()
    return await mes_ai_prediction.predict_demand(
        body["item_code"],
        body.get("history_months", 12),
        body.get("forecast_months", 3),
    )


@app.get("/api/ai/demand-prediction/{item_code}")
async def demand_prediction(item_code: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_ai_prediction.predict_demand(item_code)


@app.post("/api/ai/schedule-optimize")
async def schedule_optimize(request: Request,
                     user=Depends(auth_required)):
    return await mes_plan.schedule_optimize(await request.json())


# ── FN-020~024: Work Orders & Results ────────────────────────

@app.post("/api/work-orders")
async def create_work_order(request: Request,
                     user=Depends(auth_required)):
    return await mes_work.create_work_order(await request.json())


@app.get("/api/work-orders")
async def list_work_orders(work_date: str = None, line_id: str = None,
                           status: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_work.get_work_orders(work_date, line_id, status)


@app.get("/api/work-orders/{wo_id}")
async def get_work_order(wo_id: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_work.get_work_order_detail(wo_id)


@app.put("/api/work-orders/{wo_id}/status")
async def update_wo_status(wo_id: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_work.update_work_order_status(wo_id, await request.json())


@app.post("/api/work-results")
async def create_work_result(request: Request,
                     user=Depends(auth_required)):
    return await mes_work.create_work_result(await request.json())


@app.get("/api/dashboard/production")
async def production_dashboard(date: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_work.get_dashboard(date)


# ── FN-025~027: Quality ──────────────────────────────────────

@app.post("/api/quality/standards")
async def create_quality_standard(request: Request,
                     user=Depends(auth_required)):
    return await mes_quality.create_standard(await request.json())


@app.post("/api/quality/inspections")
async def create_inspection(request: Request,
                     user=Depends(auth_required)):
    return await mes_quality.create_inspection(await request.json())


@app.get("/api/quality/defects")
async def get_defects(start_date: str = None, end_date: str = None,
                      item_code: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_quality.get_defects(start_date, end_date, item_code)


# ── FN-028: AI Defect Prediction ─────────────────────────────

@app.post("/api/ai/defect-predict")
async def ai_defect_predict(request: Request,
                     user=Depends(auth_required)):
    return await mes_defect_predict.predict_defect_probability(
        await request.json()
    )


@app.post("/api/ai/defect-prediction")
async def defect_prediction(request: Request,
                     user=Depends(auth_required)):
    body = await request.json()
    return await mes_defect_predict.predict_defect_probability(body)


# ── FN-029~031: Inventory ────────────────────────────────────

@app.post("/api/inventory/in")
async def inventory_in(request: Request,
                     user=Depends(auth_required)):
    return await mes_inventory.inventory_in(await request.json())


@app.post("/api/inventory/out")
async def inventory_out(request: Request,
                     user=Depends(auth_required)):
    return await mes_inventory.inventory_out(await request.json())


@app.get("/api/inventory")
async def get_inventory(warehouse: str = None, category: str = None,
                        request: Request = None,
                     user=Depends(auth_required)):
    return await mes_inventory.get_inventory(warehouse, category)


@app.post("/api/inventory/move")
async def inventory_move(request: Request,
                     user=Depends(auth_required)):
    body = await request.json()
    return await mes_inventory_movement.move_inventory(
        body["item_code"], body["lot_no"], body["qty"],
        body["from_location"], body["to_location"],
    )


# ── FN-032~034: Equipment Status & AI ────────────────────────

@app.put("/api/equipments/{equip_code}/status")
async def update_equip_status(equip_code: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_equipment.update_status(equip_code, await request.json())


@app.get("/api/equipments/status")
async def equip_status_dashboard(request: Request,
                     user=Depends(auth_required)):
    return await mes_equipment.get_equipment_status()


@app.post("/api/ai/failure-predict")
async def ai_failure_predict(request: Request,
                     user=Depends(auth_required)):
    return await mes_equipment.predict_failure(await request.json())


# ── FN-035~037: Reports & Analysis ───────────────────────────

@app.get("/api/reports/production")
async def report_production(start_date: str = None, end_date: str = None,
                            group_by: str = "day", request: Request = None,
                     user=Depends(auth_required)):
    return await mes_reports.production_report(start_date, end_date, group_by)


@app.get("/api/reports/quality")
async def report_quality(start_date: str = None, end_date: str = None,
                         item_code: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_reports.quality_report(start_date, end_date, item_code)


@app.post("/api/ai/insights")
async def analysis_insights(request: Request,
                     user=Depends(auth_required)):
    try:
        data = await request.json()
    except Exception:
        data = {}
    return await mes_reports.ai_insights(data)


# ── LOT Traceability (GS: KS X 9003) ────────────────────────

@app.get("/api/lot/trace/{lot_no}")
async def lot_trace(lot_no: str, request: Request,
                     user=Depends(auth_required)):
    return await mes_inventory.trace_lot(lot_no)


# ── Legacy / Infrastructure ──────────────────────────────────

@app.get("/api/mes/data")
async def get_mes_data(request: Request,
                     user=Depends(auth_required)):
    return await mes_dashboard.get_production_dashboard_data()


@app.get("/api/network/flows")
async def get_flows(request: Request,
                     user=Depends(auth_required)):
    try:
        flows = k8s_service.get_flows()
        return {"status": "success", "flows": flows}
    except Exception:
        return {"status": "success", "flows": []}


@app.get("/api/network/topology")
async def get_topology(request: Request,
                     user=Depends(auth_required)):
    try:
        flows = k8s_service.get_flows()
    except Exception:
        flows = []
    nodes = set()
    edges = {}
    for f in flows:
        try:
            src = (f.get("source", {}).get("pod_name")
                   or f.get("src", {}).get("pod_name"))
            dst = (f.get("destination", {}).get("pod_name")
                   or f.get("dst", {}).get("pod_name"))
        except (AttributeError, TypeError):
            continue
        if not src or not dst:
            continue
        nodes.add(src)
        nodes.add(dst)
        key = (src, dst)
        edges[key] = edges.get(key, 0) + 1
    return {
        "status": "success",
        "nodes": [{"id": n, "label": n} for n in sorted(nodes)],
        "edges": [
            {"source": s, "target": t, "count": c}
            for (s, t), c in edges.items()
        ],
    }


@app.get("/api/network/hubble-flows")
async def get_hubble_flows(last: int = 50, request: Request = None,
                     user=Depends(auth_required)):
    try:
        flows = k8s_service.get_hubble_flows(min(last, 200))
        return {"status": "success", "flows": flows, "total": len(flows)}
    except Exception:
        return {"status": "success", "flows": [], "total": 0}


@app.get("/api/network/service-map")
async def get_service_map(request: Request,
                     user=Depends(auth_required)):
    try:
        smap = k8s_service.get_service_map()
        return {"status": "success", **smap}
    except Exception:
        return {"status": "success", "services": [], "connections": []}


@app.get("/api/infra/status")
async def get_infra(request: Request,
                     user=Depends(auth_required)):
    try:
        infra = await sys_logic.get_infra() if callable(
            getattr(sys_logic, "get_infra", None)
        ) else {}
    except Exception:
        infra = {}
    cpu_str = infra.get("cpu") or infra.get("cpu_load") or infra.get("cpuUsage")
    mem_str = infra.get("mem") or infra.get("memory") or infra.get("memory_usage")

    def pct(v):
        if v is None:
            return 0.0, "0%"
        if isinstance(v, (int, float)):
            return float(v), f"{float(v):.1f}%"
        s = str(v).strip().rstrip("%")
        try:
            n = float(s)
            return n, f"{n:.1f}%"
        except ValueError:
            return 0.0, "0%"

    cn, cf = pct(cpu_str)
    mn, mf = pct(mem_str)
    return {"cpu_load": cn, "memory_usage": mn, "cpu": cf, "mem": mf}


@app.get("/api/k8s/pods")
async def get_pods(request: Request,
                     user=Depends(auth_required)):
    return sys_logic.get_pods()


@app.get("/api/k8s/logs/{name}")
async def get_pod_logs(name: str, request: Request,
                     user=Depends(auth_required)):
    try:
        return PlainTextResponse(str(k8s_service.get_logs(name)))
    except Exception:
        return PlainTextResponse("Logs Unavailable")


# ── FN-038~040: SPC ──────────────────────────────────────────

@app.get("/api/quality/spc/{item_code}")
async def spc_chart(item_code: str, check_name: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_spc.get_spc_chart(item_code, check_name)


@app.post("/api/quality/spc/rules")
async def create_spc_rule(request: Request, user=Depends(auth_required)):
    return await mes_spc.create_spc_rule(await request.json())


@app.get("/api/quality/cpk/{item_code}")
async def cpk_analysis(item_code: str, check_name: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_spc.get_cpk(item_code, check_name)


# ── FN-041~043: CAPA ─────────────────────────────────────────

@app.post("/api/quality/capa")
async def create_capa(request: Request, user=Depends(auth_required)):
    return await mes_capa.create_capa(await request.json())


@app.put("/api/quality/capa/{capa_id}/status")
async def update_capa_status(capa_id: str, request: Request,
                             user=Depends(auth_required)):
    return await mes_capa.update_capa_status(capa_id, await request.json())


@app.get("/api/quality/capa")
async def list_capa(status: str = None, capa_type: str = None,
                    assigned_to: str = None, request: Request = None,
                    user=Depends(auth_required)):
    return await mes_capa.get_capa_list(status, capa_type, assigned_to)


# ── FN-044~045: OEE ──────────────────────────────────────────

@app.get("/api/equipment/oee/{equip_code}")
async def equip_oee(equip_code: str, start_date: str = None,
                    end_date: str = None, request: Request = None,
                    user=Depends(auth_required)):
    return await mes_oee.get_oee(equip_code, start_date, end_date)


@app.get("/api/equipment/oee/dashboard")
async def oee_dashboard(request: Request, user=Depends(auth_required)):
    return await mes_oee.get_oee_dashboard()


# ── FN-046~047: Notifications ────────────────────────────────

@app.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    # JWT에서 user_id 추출
    token = websocket.query_params.get("token", "")
    user_payload = await mes_auth.verify_token(token) if token else None
    user_id = user_payload.get("user_id", "anonymous") if isinstance(user_payload, dict) else "anonymous"

    await mes_notification.manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 클라이언트 메시지 처리 (ping/pong 등)
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        mes_notification.manager.disconnect(websocket, user_id)


@app.get("/api/notifications")
async def list_notifications(unread_only: bool = False, limit: int = 50,
                             request: Request = None, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_notification.get_notifications(user_id, unread_only, limit)


@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, request: Request,
                                  user=Depends(auth_required)):
    return await mes_notification.mark_read(notification_id)


@app.get("/api/notifications/settings")
async def get_notif_settings(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_notification.get_notification_settings(user_id)


@app.post("/api/notifications/settings")
async def update_notif_settings(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_notification.update_notification_settings(user_id, await request.json())


# ── FN-048: LOT Genealogy ────────────────────────────────────

@app.get("/api/lot/genealogy/{lot_no}")
async def lot_genealogy(lot_no: str, direction: str = "both",
                        request: Request = None, user=Depends(auth_required)):
    return await mes_lot_trace.trace_genealogy(lot_no, direction)


# ── REQ-052: Barcode/QR ──────────────────────────────────────

@app.post("/api/barcode/generate")
async def barcode_generate(request: Request, user=Depends(auth_required)):
    return await mes_barcode.generate_barcode(await request.json())


@app.post("/api/barcode/scan")
async def barcode_scan(request: Request, user=Depends(auth_required)):
    return await mes_barcode.scan_barcode(await request.json())


# ── REQ-053: Electronic Work Instructions ────────────────────

@app.post("/api/work-instructions")
async def create_wi(request: Request, user=Depends(auth_required)):
    return await mes_ewi.create_work_instruction(await request.json())


@app.get("/api/work-instructions")
async def list_wi(wo_no: str = None, status: str = None,
                  request: Request = None, user=Depends(auth_required)):
    return await mes_ewi.get_work_instructions(wo_no, status)


@app.get("/api/work-instructions/{wi_id}")
async def get_wi(wi_id: str, request: Request = None,
                 user=Depends(auth_required)):
    return await mes_ewi.get_work_instruction_detail(wi_id)


@app.post("/api/work-instructions/{wi_id}/steps/{step_no}/sign")
async def sign_wi_step(wi_id: str, step_no: int, request: Request,
                       user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_ewi.sign_step(wi_id, step_no, user_id)


# ── REQ-054: NCR (부적합품 관리) ─────────────────────────────

@app.post("/api/quality/ncr")
async def create_ncr(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_ncr.create_ncr(await request.json(), user_id)


@app.get("/api/quality/ncr")
async def list_ncr(status: str = None, lot_no: str = None,
                   request: Request = None, user=Depends(auth_required)):
    return await mes_ncr.get_ncr_list(status, lot_no)


@app.put("/api/quality/ncr/{ncr_id}/disposition")
async def ncr_disposition(ncr_id: str, request: Request,
                          user=Depends(auth_required)):
    return await mes_ncr.update_ncr_disposition(ncr_id, await request.json())


# ── REQ-055: SPC Auto-Actions ────────────────────────────────

@app.post("/api/quality/spc/auto-actions")
async def spc_auto_act(request: Request, user=Depends(auth_required)):
    return await mes_spc.spc_auto_actions(await request.json())


# ── REQ-056: Shipment Disposition ────────────────────────────

@app.post("/api/quality/disposition")
async def create_disp(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_disposition.create_disposition(await request.json(), user_id)


@app.get("/api/quality/disposition")
async def list_disp(lot_no: str = None, decision: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_disposition.get_dispositions(lot_no, decision)


# ── REQ-057: FPY ─────────────────────────────────────────────

@app.get("/api/kpi/fpy")
async def kpi_fpy(process_code: str = None, item_code: str = None,
                  start_date: str = None, end_date: str = None,
                  request: Request = None, user=Depends(auth_required)):
    return await mes_kpi.get_fpy(process_code, item_code, start_date, end_date)


# ── REQ-058: Maintenance KPI (MTTF/MTTR/MTBF) ───────────────

@app.get("/api/kpi/maintenance/{equip_code}")
async def kpi_maintenance(equip_code: str,
                          start_date: str = None, end_date: str = None,
                          request: Request = None,
                          user=Depends(auth_required)):
    return await mes_kpi.get_maintenance_kpi(equip_code, start_date, end_date)


# ── FN-049~051: CMMS 유지보전 ────────────────────────────────

@app.post("/api/maintenance/pm")
async def create_pm(request: Request, user=Depends(auth_required)):
    return await mes_maintenance.create_pm_schedule(await request.json())


@app.get("/api/maintenance/pm")
async def list_pm(equip_code: str = None, status: str = None,
                  request: Request = None, user=Depends(auth_required)):
    return await mes_maintenance.get_pm_schedules(equip_code, status)


@app.post("/api/maintenance/work-orders")
async def create_mwo(request: Request, user=Depends(auth_required)):
    return await mes_maintenance.create_maintenance_order(await request.json())


@app.put("/api/maintenance/work-orders/{mo_id}")
async def update_mwo(mo_id: str, request: Request, user=Depends(auth_required)):
    return await mes_maintenance.update_maintenance_order(mo_id, await request.json())


@app.get("/api/maintenance/history/{equip_code}")
async def maint_history(equip_code: str, mo_type: str = None,
                        start_date: str = None, end_date: str = None,
                        request: Request = None, user=Depends(auth_required)):
    return await mes_maintenance.get_maintenance_history(
        equip_code, mo_type, start_date, end_date)


# ── FN-052~053: 레시피 관리 ──────────────────────────────────

@app.post("/api/recipes")
async def create_recipe(request: Request, user=Depends(auth_required)):
    return await mes_recipe.create_recipe(await request.json())


@app.get("/api/recipes")
async def list_recipes(item_code: str = None, process_code: str = None,
                       status: str = None, request: Request = None,
                       user=Depends(auth_required)):
    return await mes_recipe.get_recipes(item_code, process_code, status)


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: int, compare_version: int = None,
                     request: Request = None, user=Depends(auth_required)):
    return await mes_recipe.get_recipe_detail(recipe_id, compare_version)


@app.put("/api/recipes/{recipe_id}/approve")
async def approve_recipe(recipe_id: int, request: Request,
                         user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_recipe.approve_recipe(recipe_id, user_id)


# ── FN-054~055: MQTT / 센서 데이터 ──────────────────────────

@app.post("/api/datacollect/mqtt/config")
async def save_mqtt(request: Request, user=Depends(admin_required)):
    return await mes_datacollect.save_mqtt_config(await request.json())


@app.get("/api/datacollect/mqtt/config")
async def list_mqtt(request: Request = None, user=Depends(auth_required)):
    return await mes_datacollect.get_mqtt_configs()


@app.get("/api/datacollect/realtime/{equip_code}")
async def realtime_sensor(equip_code: str, sensor_type: str = None,
                          minutes: int = 30, interval: str = "raw",
                          request: Request = None, user=Depends(auth_required)):
    return await mes_datacollect.get_realtime_sensor(
        equip_code, sensor_type, minutes, interval)


@app.post("/api/datacollect/sensor")
async def insert_sensor(request: Request, user=Depends(auth_required)):
    return await mes_datacollect.insert_sensor_data(await request.json())


# ── FN-056~057: 문서 관리 DMS ────────────────────────────────

@app.post("/api/documents")
async def create_doc(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_document.create_document(await request.json(), user_id)


@app.get("/api/documents")
async def list_docs(doc_type: str = None, item_code: str = None,
                    process_code: str = None, keyword: str = None,
                    status: str = None, request: Request = None,
                    user=Depends(auth_required)):
    return await mes_document.get_documents(
        doc_type, item_code, process_code, keyword, status)


@app.put("/api/documents/{doc_id}/approve")
async def approve_doc(doc_id: int, request: Request,
                      user=Depends(admin_required)):
    return await mes_document.approve_document(doc_id)


# ── FN-058: 노동 관리 / 스킬 매트릭스 ───────────────────────

@app.get("/api/labor/skills")
async def get_skills(process_code: str = None, skill_level: str = None,
                     worker_id: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_labor.get_worker_skills(process_code, skill_level, worker_id)


@app.post("/api/labor/skills")
async def upsert_skill(request: Request, user=Depends(admin_required)):
    return await mes_labor.upsert_worker_skill(await request.json())


# ── Phase 3: ERP 연동 (FN-059) ──────────────────────────────

@app.post("/api/erp/sync-config")
async def create_erp_sync(request: Request, user=Depends(admin_required)):
    return await mes_erp.create_sync_config(await request.json())


@app.get("/api/erp/sync-config")
async def get_erp_syncs(request: Request = None, user=Depends(auth_required)):
    return await mes_erp.get_sync_configs()


@app.post("/api/erp/sync/{config_id}/execute")
async def execute_erp_sync(config_id: int, request: Request,
                           user=Depends(admin_required)):
    return await mes_erp.execute_sync(config_id, user.get("user_id", "system"))


@app.get("/api/erp/sync-logs")
async def get_erp_logs(config_id: int = None, status: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_erp.get_sync_logs(config_id, status)


# ── Phase 3: OPC-UA 연동 (FN-060~061) ───────────────────────

@app.post("/api/opcua/config")
async def create_opcua_cfg(request: Request, user=Depends(admin_required)):
    return await mes_opcua.save_opcua_config(await request.json())


@app.get("/api/opcua/config")
async def get_opcua_cfgs(request: Request = None, user=Depends(auth_required)):
    return await mes_opcua.get_opcua_configs()


@app.get("/api/opcua/status")
async def opcua_status(request: Request = None, user=Depends(auth_required)):
    return await mes_opcua.get_opcua_status()


# ── Phase 3: 감사 추적 (FN-062~063) ─────────────────────────

@app.get("/api/audit")
async def get_audits(entity_type: str = None, entity_id: str = None,
                     user_id: str = None, action: str = None,
                     date_from: str = None, date_to: str = None,
                     page: int = 1, page_size: int = 50,
                     request: Request = None, user=Depends(admin_required)):
    return await mes_audit.get_audit_logs(
        entity_type, entity_id, user_id, action, date_from, date_to, page, page_size)


@app.get("/api/audit/summary")
async def audit_summary(request: Request = None, user=Depends(admin_required)):
    return await mes_audit.get_audit_summary()


# ── Phase 3: 다국어 i18n (FN-064) ───────────────────────────

@app.get("/api/i18n/translations")
async def get_i18n(locale: str = None, request: Request = None,
                   user=Depends(auth_required)):
    return await mes_i18n.get_translations(locale)


@app.get("/api/i18n/locales")
async def get_locales(request: Request = None, user=Depends(auth_required)):
    return await mes_i18n.get_supported_locales()


@app.post("/api/i18n/translations")
async def upsert_i18n(request: Request, user=Depends(admin_required)):
    return await mes_i18n.upsert_translation(await request.json())


@app.delete("/api/i18n/translations/{locale}/{msg_key}")
async def delete_i18n(locale: str, msg_key: str, request: Request,
                      user=Depends(admin_required)):
    return await mes_i18n.delete_translation(locale, msg_key)


# ── Phase 3: 리소스 관리 (FN-066) ───────────────────────────

@app.get("/api/resources")
async def get_res(resource_type: str = None, status: str = None,
                  keyword: str = None, request: Request = None,
                  user=Depends(auth_required)):
    return await mes_resource.get_resources(resource_type, status, keyword)


@app.post("/api/resources")
async def create_res(request: Request, user=Depends(admin_required)):
    return await mes_resource.create_resource(await request.json())


@app.put("/api/resources/{resource_id}/status")
async def update_res_status(resource_id: int, request: Request,
                            user=Depends(admin_required)):
    return await mes_resource.update_resource_status(resource_id, await request.json())


@app.get("/api/resources/summary")
async def res_summary(request: Request = None, user=Depends(auth_required)):
    return await mes_resource.get_resource_summary()


# ── Phase 2+: MSA/Gage R&R (REQ-059) ────────────────────────

@app.post("/api/msa/studies")
async def create_msa(request: Request, user=Depends(auth_required)):
    return await mes_msa.create_study(await request.json())


@app.get("/api/msa/studies")
async def get_msa_list(gauge_code: str = None, study_type: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_msa.get_studies(gauge_code, study_type)


@app.post("/api/msa/studies/{study_id}/measurements")
async def add_msa_meas(study_id: int, request: Request, user=Depends(auth_required)):
    return await mes_msa.add_measurements(study_id, await request.json())


@app.post("/api/msa/studies/{study_id}/calculate")
async def calc_grr(study_id: int, request: Request, user=Depends(auth_required)):
    return await mes_msa.calculate_grr(study_id)


# ── Phase 2+: FMEA (REQ-061) ────────────────────────────────

@app.post("/api/fmea")
async def create_fmea_doc(request: Request, user=Depends(auth_required)):
    return await mes_fmea.create_fmea(await request.json())


@app.get("/api/fmea")
async def list_fmea(item_code: str = None, status: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_fmea.get_fmea_list(item_code, status)


@app.get("/api/fmea/{fmea_id}")
async def detail_fmea(fmea_id: int, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_fmea.get_fmea_detail(fmea_id)


@app.post("/api/fmea/{fmea_id}/items")
async def add_fmea_item_ep(fmea_id: int, request: Request,
                           user=Depends(auth_required)):
    return await mes_fmea.add_fmea_item(fmea_id, await request.json())


# ── Phase 2+: 에너지 관리 (REQ-063) ─────────────────────────

@app.post("/api/energy")
async def record_energy_ep(request: Request, user=Depends(auth_required)):
    return await mes_energy.record_energy(await request.json())


@app.get("/api/energy/dashboard")
async def energy_dash(equip_code: str = None, energy_type: str = None,
                      hours: int = 24, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_energy.get_energy_dashboard(equip_code, energy_type, hours)


@app.get("/api/energy/per-unit")
async def energy_per_unit(request: Request = None, user=Depends(auth_required)):
    return await mes_energy.get_energy_per_unit()


# ── Phase 2+: 교정 관리 (REQ-064) ───────────────────────────

@app.post("/api/calibration/gauges")
async def create_gauge_ep(request: Request, user=Depends(admin_required)):
    return await mes_calibration.create_gauge(await request.json())


@app.get("/api/calibration/gauges")
async def list_gauges(status: str = None, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_calibration.get_gauges(status)


@app.post("/api/calibration/gauges/{calibration_id}/records")
async def record_calib(calibration_id: int, request: Request,
                       user=Depends(auth_required)):
    return await mes_calibration.record_calibration(calibration_id, await request.json())


# ── Phase 2+: SQM 공급업체 품질 (REQ-065) ───────────────────

@app.post("/api/sqm/suppliers")
async def create_supplier_ep(request: Request, user=Depends(admin_required)):
    return await mes_sqm.create_supplier(await request.json())


@app.get("/api/sqm/suppliers")
async def list_suppliers(asl_status: str = None, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_sqm.get_suppliers(asl_status)


@app.post("/api/sqm/scar")
async def create_scar_ep(request: Request, user=Depends(auth_required)):
    return await mes_sqm.create_scar(await request.json())


@app.get("/api/sqm/scar")
async def list_scar(supplier_id: int = None, status: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_sqm.get_scars(supplier_id, status)


@app.post("/api/sqm/suppliers/{supplier_id}/score")
async def update_score(supplier_id: int, request: Request,
                       user=Depends(admin_required)):
    return await mes_sqm.update_supplier_score(supplier_id)


# ── Phase 2+: 자동디스패칭 (REQ-066) ────────────────────────

@app.post("/api/dispatch/auto")
async def auto_dispatch_ep(request: Request, user=Depends(admin_required)):
    body = await request.json()
    return await mes_dispatch.auto_dispatch(body.get("plan_id"))


@app.post("/api/dispatch/backflush")
async def backflush_ep(request: Request, user=Depends(auth_required)):
    body = await request.json()
    return await mes_dispatch.backflush(body.get("wo_code", ""), body.get("good_qty", 0))


# ── Phase 2+: 셋업시간 매트릭스 (REQ-067) ───────────────────

@app.post("/api/setup-matrix")
async def upsert_setup_ep(request: Request, user=Depends(auth_required)):
    return await mes_setup.upsert_setup(await request.json())


@app.post("/api/setup-matrix/actual")
async def record_setup_actual(request: Request, user=Depends(auth_required)):
    return await mes_setup.record_actual(await request.json())


@app.get("/api/setup-matrix")
async def get_setup_matrix(equip_code: str = None, request: Request = None,
                           user=Depends(auth_required)):
    return await mes_setup.get_matrix(equip_code)


# ── Phase 2+: WO 원가추적 (REQ-068) ─────────────────────────

@app.post("/api/costing")
async def add_cost_ep(request: Request, user=Depends(auth_required)):
    return await mes_costing.add_cost(await request.json())


@app.get("/api/costing/{wo_code}")
async def get_wo_cost_ep(wo_code: str, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_costing.get_wo_cost(wo_code)


@app.get("/api/costing")
async def cost_summary(request: Request = None, user=Depends(auth_required)):
    return await mes_costing.get_cost_summary()


# ── Phase 2+: 대시보드 빌더 (REQ-069) ───────────────────────

@app.post("/api/dashboard-builder/layouts")
async def save_dash(request: Request, user=Depends(auth_required)):
    return await mes_dashboard_builder.save_layout(
        await request.json(), user.get("user_id", ""))


@app.get("/api/dashboard-builder/layouts")
async def list_dash(request: Request = None, user=Depends(auth_required)):
    return await mes_dashboard_builder.get_layouts(user.get("user_id", ""))


@app.get("/api/dashboard-builder/layouts/{layout_id}")
async def detail_dash(layout_id: int, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_dashboard_builder.get_layout_detail(layout_id)


@app.delete("/api/dashboard-builder/layouts/{layout_id}")
async def delete_dash(layout_id: int, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_dashboard_builder.delete_layout(layout_id, user.get("user_id", ""))


# ── Phase 2+: 리포트 빌더 (REQ-070) ─────────────────────────

@app.post("/api/report-builder/templates")
async def create_rpt(request: Request, user=Depends(auth_required)):
    return await mes_report_builder.create_template(
        await request.json(), user.get("user_id", ""))


@app.get("/api/report-builder/templates")
async def list_rpt(request: Request = None, user=Depends(auth_required)):
    return await mes_report_builder.get_templates()


@app.post("/api/report-builder/templates/{template_id}/execute")
async def exec_rpt(template_id: int, request: Request,
                   user=Depends(auth_required)):
    return await mes_report_builder.execute_report(template_id)


# ── Phase 3+: 배치실행엔진 + eBR (REQ-071/072) ──────────────

@app.post("/api/batch")
async def create_batch_ep(request: Request, user=Depends(auth_required)):
    return await mes_batch.create_batch(await request.json())


@app.get("/api/batch")
async def list_batch(status: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_batch.get_batches(status)


@app.put("/api/batch/{batch_id}/transition")
async def transition_batch_ep(batch_id: int, request: Request,
                              user=Depends(auth_required)):
    return await mes_batch.transition_batch(batch_id, await request.json())


@app.post("/api/batch/{batch_id}/ebr")
async def add_ebr(batch_id: int, request: Request,
                  user=Depends(auth_required)):
    return await mes_batch.add_ebr_record(batch_id, await request.json())


@app.get("/api/batch/{batch_id}/ebr")
async def get_ebr_ep(batch_id: int, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_batch.get_ebr(batch_id)


# ── Phase 3+: 설계변경관리 ECM (REQ-073) ────────────────────

@app.post("/api/ecm")
async def create_ecr_ep(request: Request, user=Depends(auth_required)):
    return await mes_ecm.create_ecr(await request.json())


@app.get("/api/ecm")
async def list_ecr(status: str = None, change_type: str = None,
                   request: Request = None, user=Depends(auth_required)):
    return await mes_ecm.get_ecr_list(status, change_type)


@app.put("/api/ecm/{ecr_id}/transition")
async def transition_ecr_ep(ecr_id: int, request: Request,
                            user=Depends(admin_required)):
    return await mes_ecm.transition_ecr(ecr_id, await request.json())


# ── Phase 3+: 복합라우팅 (REQ-074) ──────────────────────────

@app.post("/api/complex-routing")
async def create_crouting(request: Request, user=Depends(admin_required)):
    return await mes_complex_routing.create_routing(await request.json())


@app.get("/api/complex-routing")
async def get_crouting(routing_code: str = None, item_code: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_complex_routing.get_routing(routing_code, item_code)


# ── Phase 3+: 멀티사이트 관리 (REQ-075) ─────────────────────

@app.post("/api/sites")
async def create_site_ep(request: Request, user=Depends(admin_required)):
    return await mes_multisite.create_site(await request.json())


@app.get("/api/sites")
async def list_sites(request: Request = None, user=Depends(auth_required)):
    return await mes_multisite.get_sites()


@app.get("/api/sites/{site_id}/dashboard")
async def site_dashboard(site_id: int, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_multisite.get_site_dashboard(site_id)


# ── Health Check (no auth) ───────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "6.0"}


@app.get("/api/version")
async def api_version():
    """NFR-018: API version info. Supports /api/v1/ prefix via middleware."""
    return {
        "api_version": "v1",
        "app_version": "6.0",
        "supported_versions": ["v1"],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
