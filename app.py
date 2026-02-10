from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api_modules import mes_logic, sys_logic, mes_execution
import uvicorn

app = FastAPI(title="KNU Modular MES v21.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/mes/data")
async def mes_data(): return mes_logic.get_full_data()

@app.post("/api/mes/plans")
async def plan_post(req: Request):
    return mes_logic.add_plan(await req.json())

@app.get("/api/k8s/pods")
async def pods(): return sys_logic.get_pods()

@app.get("/api/network/flows")
async def flows(): return sys_logic.get_flows()

@app.get("/api/infra/status")
async def infra(): return sys_logic.get_infra()

@app.post("/api/mes/work_results")
async def work_results_post(req: Request):
    data = await req.json()
    return await mes_execution.register_work_performance(
        wo_id=data.get("wo_id"),
        good_qty=data.get("good_qty"),
        defect_qty=data.get("defect_qty"),
        worker_id=data.get("worker_id"),
        start_time=datetime.fromisoformat(data.get("start_time")) if data.get("start_time") else None,
        end_time=datetime.fromisoformat(data.get("end_time")) if data.get("end_time") else None,
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
