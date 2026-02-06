from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api_modules import mes_logic, sys_logic
import uvicorn

app = FastAPI(title="KNU Modular MES v19.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 로그에 찍힌 프론트엔드의 호출 주소와 정확히 일치시킴
@app.get("/api/mes/data")
async def mes_data(): return mes_logic.get_full_data()

@app.post("/api/mes/plans")
async def plan_post(req: Request):
    res = mes_logic.add_plan(await req.json())
    return {"success": res}

@app.get("/api/k8s/pods")
async def k8s_pods(): return sys_logic.get_pods()

@app.get("/api/network/flows")
async def network_flows(): return sys_logic.get_flows()

@app.get("/api/infra/status")
async def infra_status(): return sys_logic.get_infra()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
