"""MES Backend Application.

FastAPI-based Manufacturing Execution System API server.
Full FN-001 ~ FN-037 implementation.
"""

import os

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import uvicorn

from api_modules import (
    k8s_service,
    mes_ai_prediction,
    mes_auth,
    mes_bom,
    mes_dashboard,
    mes_defect_predict,
    mes_equipment,
    mes_inventory,
    mes_inventory_status,
    mes_items,
    mes_plan,
    mes_process,
    mes_quality,
    mes_reports,
    mes_work,
    sys_logic,
)

app = FastAPI(title="KNU MES API", version="3.0")

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
)


# ── FN-001~003: Auth ─────────────────────────────────────

@app.post("/api/auth/login")
async def login(request: Request):
    body = await request.json()
    return await mes_auth.login(body["user_id"], body["password"])


@app.post("/api/auth/register")
async def register(request: Request):
    return await mes_auth.register(await request.json())


@app.get("/api/auth/permissions/{user_id}")
async def get_permissions(user_id: str):
    return await mes_auth.get_permissions(user_id)


# ── FN-004~007: Items ────────────────────────────────────

@app.post("/api/items")
async def create_item(request: Request):
    return await mes_items.create_item(await request.json())


@app.get("/api/items")
async def list_items(keyword: str = None, category: str = None,
                     page: int = 1, size: int = 20):
    return await mes_items.get_items(keyword, category, page, size)


@app.get("/api/items/{item_code}")
async def get_item(item_code: str):
    return await mes_items.get_item_detail(item_code)


@app.put("/api/items/{item_code}")
async def update_item(item_code: str, request: Request):
    return await mes_items.update_item(item_code, await request.json())


# ── FN-008~009: BOM ──────────────────────────────────────

@app.post("/api/bom")
async def create_bom(request: Request):
    return await mes_bom.create_bom(await request.json())


@app.get("/api/bom/explode/{item_code}")
async def explode_bom(item_code: str, qty: float = 1):
    return await mes_bom.explode_bom(item_code, qty)


# ── FN-010~012: Process & Routing ────────────────────────

@app.post("/api/processes")
async def create_process(request: Request):
    return await mes_process.create_process(await request.json())


@app.post("/api/routings")
async def create_routing(request: Request):
    return await mes_process.create_routing(await request.json())


@app.get("/api/routings/{item_code}")
async def get_routing(item_code: str):
    return await mes_process.get_routing(item_code)


# ── FN-013~014: Equipment ────────────────────────────────

@app.post("/api/equipments")
async def create_equipment(request: Request):
    return await mes_equipment.create_equipment(await request.json())


@app.get("/api/equipments")
async def list_equipments(process_code: str = None, status: str = None):
    return await mes_equipment.get_equipments(process_code, status)


# ── FN-015~017: Plans ────────────────────────────────────

@app.post("/api/plans")
async def create_plan(request: Request):
    return await mes_plan.create_plan(await request.json())


@app.get("/api/plans")
async def list_plans(start_date: str = None, end_date: str = None,
                     status: str = None, page: int = 1):
    return await mes_plan.get_plans(start_date, end_date, status, page)


@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: int):
    return await mes_plan.get_plan_detail(plan_id)


# ── FN-018~019: AI Planning ──────────────────────────────

@app.post("/api/ai/demand-forecast")
async def demand_forecast(request: Request):
    body = await request.json()
    return await mes_ai_prediction.predict_demand(
        body["item_code"],
        body.get("history_months", 12),
        body.get("forecast_months", 3),
    )


@app.get("/api/ai/demand-prediction/{item_code}")
async def demand_prediction(item_code: str):
    return await mes_ai_prediction.predict_demand(item_code)


@app.post("/api/ai/schedule-optimize")
async def schedule_optimize(request: Request):
    return await mes_plan.schedule_optimize(await request.json())


# ── FN-020~024: Work Orders & Results ────────────────────

@app.post("/api/work-orders")
async def create_work_order(request: Request):
    return await mes_work.create_work_order(await request.json())


@app.get("/api/work-orders")
async def list_work_orders(work_date: str = None, line_id: str = None,
                           status: str = None):
    return await mes_work.get_work_orders(work_date, line_id, status)


@app.get("/api/work-orders/{wo_id}")
async def get_work_order(wo_id: str):
    return await mes_work.get_work_order_detail(wo_id)


@app.post("/api/work-results")
async def create_work_result(request: Request):
    return await mes_work.create_work_result(await request.json())


@app.get("/api/dashboard/production")
async def production_dashboard(date: str = None):
    return await mes_work.get_dashboard(date)


# ── FN-025~027: Quality ──────────────────────────────────

@app.post("/api/quality/standards")
async def create_quality_standard(request: Request):
    return await mes_quality.create_standard(await request.json())


@app.post("/api/quality/inspections")
async def create_inspection(request: Request):
    return await mes_quality.create_inspection(await request.json())


@app.get("/api/quality/defects")
async def get_defects(start_date: str = None, end_date: str = None,
                      item_code: str = None):
    return await mes_quality.get_defects(start_date, end_date, item_code)


# ── FN-028: AI Defect Prediction ─────────────────────────

@app.post("/api/ai/defect-predict")
async def ai_defect_predict(request: Request):
    return await mes_defect_predict.predict_defect_probability(
        await request.json()
    )


@app.post("/api/ai/defect-prediction")
async def defect_prediction(request: Request):
    body = await request.json()
    return await mes_defect_predict.predict_defect_probability(body)


# ── FN-029~031: Inventory ────────────────────────────────

@app.post("/api/inventory/in")
async def inventory_in(request: Request):
    return await mes_inventory.inventory_in(await request.json())


@app.post("/api/inventory/out")
async def inventory_out(request: Request):
    return await mes_inventory.inventory_out(await request.json())


@app.get("/api/inventory")
async def get_inventory(warehouse: str = None, category: str = None):
    return await mes_inventory.get_inventory(warehouse, category)


# ── FN-032~034: Equipment Status & AI ────────────────────

@app.put("/api/equipments/{equip_code}/status")
async def update_equip_status(equip_code: str, request: Request):
    return await mes_equipment.update_status(equip_code, await request.json())


@app.get("/api/equipments/status")
async def equip_status_dashboard():
    return await mes_equipment.get_equipment_status()


@app.post("/api/ai/failure-predict")
async def ai_failure_predict(request: Request):
    return await mes_equipment.predict_failure(await request.json())


# ── FN-035~037: Reports & AI Insights ────────────────────

@app.get("/api/reports/production")
async def report_production(start_date: str = None, end_date: str = None,
                            group_by: str = "day"):
    return await mes_reports.production_report(start_date, end_date, group_by)


@app.get("/api/reports/quality")
async def report_quality(start_date: str = None, end_date: str = None,
                         item_code: str = None):
    return await mes_reports.quality_report(start_date, end_date, item_code)


@app.post("/api/ai/insights")
async def ai_insights(request: Request):
    return await mes_reports.ai_insights(await request.json())


# ── Legacy / Infrastructure ──────────────────────────────

@app.get("/api/mes/data")
async def get_mes_data():
    return await mes_dashboard.get_production_dashboard_data()


@app.get("/api/network/flows")
async def get_flows():
    try:
        flows = k8s_service.get_flows()
        return {"status": "success", "flows": flows}
    except Exception:
        return {"status": "success", "flows": []}


@app.get("/api/network/topology")
async def get_topology():
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
async def get_hubble_flows(last: int = 50):
    try:
        flows = k8s_service.get_hubble_flows(min(last, 200))
        return {"status": "success", "flows": flows, "total": len(flows)}
    except Exception:
        return {"status": "success", "flows": [], "total": 0}


@app.get("/api/network/service-map")
async def get_service_map():
    try:
        smap = k8s_service.get_service_map()
        return {"status": "success", **smap}
    except Exception:
        return {"status": "success", "services": [], "connections": []}


@app.get("/api/infra/status")
async def get_infra():
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
async def get_pods():
    return sys_logic.get_pods()


@app.get("/api/k8s/logs/{name}")
async def get_pod_logs(name: str):
    try:
        return PlainTextResponse(str(k8s_service.get_logs(name)))
    except Exception:
        return PlainTextResponse("Logs Unavailable")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
