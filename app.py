from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_modules import mes_dashboard, mes_inventory_status, sys_logic
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/mes/data")
async def get_mes_data(): return await mes_dashboard.get_production_dashboard_data()

@app.get("/api/network/flows")
async def get_flows(): return {"status": "success", "flows": []}

@app.get("/api/infra/status")
async def get_infra(): return {"cpu_load": 15, "memory_usage": 40}

@app.get("/api/k8s/pods")
async def get_pods(): return sys_logic.get_pods()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
