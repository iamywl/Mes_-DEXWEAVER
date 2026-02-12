from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_modules import mes_dashboard, mes_inventory_status, sys_logic, k8s_service
from fastapi.responses import PlainTextResponse
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/mes/data")
async def get_mes_data(): return await mes_dashboard.get_production_dashboard_data()

@app.get("/api/network/flows")
async def get_flows():
    """Return raw flow events from Hubble (if available).

    Response: { status: 'success', flows: [ ... ] }
    """
    try:
        flows = k8s_service.get_flows()
        return {"status": "success", "flows": flows}
    except Exception:
        return {"status": "success", "flows": []}


@app.get("/api/network/topology")
async def get_topology():
    """Aggregate flows into a simple topology (nodes + edges).

    Nodes: list of pod names
    Edges: { source, target, count }
    """
    try:
        flows = k8s_service.get_flows()
    except Exception:
        flows = []

    nodes = set()
    edges = {}
    for f in flows:
        src = None
        dst = None
        try:
            src = f.get('source', {}).get('pod_name') or f.get('src', {}).get('pod_name')
            dst = f.get('destination', {}).get('pod_name') or f.get('dst', {}).get('pod_name')
        except Exception:
            continue
        if not src or not dst:
            continue
        nodes.add(src)
        nodes.add(dst)
        key = (src, dst)
        edges[key] = edges.get(key, 0) + 1

    edges_list = [{"source": s, "target": t, "count": c} for (s, t), c in edges.items()]
    nodes_list = [{"id": n, "label": n} for n in sorted(nodes)]
    return {"status": "success", "nodes": nodes_list, "edges": edges_list}

@app.get("/api/infra/status")
async def get_infra():
    """Return normalized infrastructure metrics.

    Response contains both numeric values (for tests/clients) and
    formatted strings (for frontend display):

    - `cpu_load`: number (percentage, e.g. 15.0)
    - `memory_usage`: number (percentage, e.g. 40.0)
    - `cpu`: string with percent (e.g. "15.0%")
    - `mem`: string with percent (e.g. "40.0%")
    """
    try:
        infra = await sys_logic.get_infra() if callable(getattr(sys_logic, 'get_infra', None)) else {}
    except Exception:
        infra = {}

    # sys_logic.get_infra may return {'cpu': '12.3%', 'mem': '52%'} or similar.
    cpu_str = infra.get('cpu') or infra.get('cpu_load') or infra.get('cpuUsage') or None
    mem_str = infra.get('mem') or infra.get('memory') or infra.get('memory_usage') or None

    def parse_percent(value):
        if value is None:
            return 0.0, "0%"
        if isinstance(value, (int, float)):
            return float(value), f"{float(value):.1f}%"
        s = str(value).strip()
        if s.endswith('%'):
            try:
                num = float(s.rstrip('%'))
                return num, f"{num:.1f}%"
            except Exception:
                return 0.0, "0%"
        try:
            num = float(s)
            return num, f"{num:.1f}%"
        except Exception:
            return 0.0, "0%"

    cpu_num, cpu_fmt = parse_percent(cpu_str)
    mem_num, mem_fmt = parse_percent(mem_str)

    return {
        "cpu_load": cpu_num,
        "memory_usage": mem_num,
        "cpu": cpu_fmt,
        "mem": mem_fmt,
    }

@app.get("/api/k8s/pods")
async def get_pods():
    return sys_logic.get_pods()


@app.get("/api/k8s/logs/{name}")
async def get_pod_logs(name: str):
    """Return pod logs as plain text so frontend can display directly."""
    try:
        logs = k8s_service.get_logs(name)
        if isinstance(logs, (str, bytes)):
            return PlainTextResponse(str(logs))
        return PlainTextResponse(str(logs))
    except Exception:
        return PlainTextResponse("Logs Unavailable")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
