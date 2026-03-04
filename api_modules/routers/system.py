"""System router — Network + Infra + K8s + Health + Version + MES Data."""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from api_modules import k8s_service, sys_logic, mes_dashboard, mes_notification, mes_auth
from api_modules.auth_deps import auth_required

router = APIRouter(prefix="/api", tags=["System"])


# ── WebSocket (no prefix — mounted on app directly) ──
# NOTE: WebSocket endpoint is registered in app.py since routers
#       don't support websocket prefix well with /ws.


# ── Legacy / MES Data ──

@router.get("/mes/data")
async def get_mes_data(request: Request, user=Depends(auth_required)):
    return await mes_dashboard.get_production_dashboard_data()


# ── Network ──

@router.get("/network/flows")
async def get_flows(request: Request, user=Depends(auth_required)):
    try:
        flows = k8s_service.get_flows()
        return {"status": "success", "flows": flows}
    except Exception:
        return {"status": "success", "flows": []}


@router.get("/network/topology")
async def get_topology(request: Request, user=Depends(auth_required)):
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


@router.get("/network/hubble-flows")
async def get_hubble_flows(last: int = 50, request: Request = None,
                           user=Depends(auth_required)):
    try:
        flows = k8s_service.get_hubble_flows(min(last, 200))
        return {"status": "success", "flows": flows, "total": len(flows)}
    except Exception:
        return {"status": "success", "flows": [], "total": 0}


@router.get("/network/service-map")
async def get_service_map(request: Request, user=Depends(auth_required)):
    try:
        smap = k8s_service.get_service_map()
        return {"status": "success", **smap}
    except Exception:
        return {"status": "success", "services": [], "connections": []}


# ── Infra ──

@router.get("/infra/status")
async def get_infra(request: Request, user=Depends(auth_required)):
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


# ── K8s ──

@router.get("/k8s/pods")
async def get_pods(request: Request, user=Depends(auth_required)):
    return sys_logic.get_pods()


@router.get("/k8s/logs/{name}")
async def get_pod_logs(name: str, request: Request, user=Depends(auth_required)):
    try:
        return PlainTextResponse(str(k8s_service.get_logs(name)))
    except Exception:
        return PlainTextResponse("Logs Unavailable")


# ── Health (no auth) ──

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "6.0"}


@router.get("/version")
async def api_version():
    """NFR-018: API version info."""
    return {
        "api_version": "v1",
        "app_version": "6.0",
        "supported_versions": ["v1"],
    }
