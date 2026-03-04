"""AI router — Demand forecast + Defect prediction + Failure prediction + Insights."""

from fastapi import APIRouter, Depends, Request
from api_modules import mes_ai_prediction, mes_defect_predict, mes_equipment, mes_reports, mes_plan
from api_modules.auth_deps import auth_required

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/demand-forecast")
async def demand_forecast(request: Request, user=Depends(auth_required)):
    body = await request.json()
    return await mes_ai_prediction.predict_demand(
        body["item_code"],
        body.get("history_months", 12),
        body.get("forecast_months", 3),
    )


@router.get("/demand-prediction/{item_code}")
async def demand_prediction(item_code: str, request: Request,
                            user=Depends(auth_required)):
    return await mes_ai_prediction.predict_demand(item_code)


@router.post("/schedule-optimize")
async def schedule_optimize(request: Request, user=Depends(auth_required)):
    return await mes_plan.schedule_optimize(await request.json())


@router.post("/defect-predict")
async def ai_defect_predict(request: Request, user=Depends(auth_required)):
    return await mes_defect_predict.predict_defect_probability(await request.json())


@router.post("/defect-prediction")
async def defect_prediction(request: Request, user=Depends(auth_required)):
    return await mes_defect_predict.predict_defect_probability(await request.json())


@router.post("/failure-predict")
async def ai_failure_predict(request: Request, user=Depends(auth_required)):
    return await mes_equipment.predict_failure(await request.json())


@router.post("/insights")
async def analysis_insights(request: Request, user=Depends(auth_required)):
    try:
        data = await request.json()
    except Exception:
        data = {}
    return await mes_reports.ai_insights(data)
