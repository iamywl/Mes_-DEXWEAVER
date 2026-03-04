"""Production router — Plans + Work Orders + Dashboard + Dispatch + Setup + Batch + ComplexRouting + Costing."""

from fastapi import APIRouter, Depends, Request
from api_modules import (mes_plan, mes_work, mes_dispatch, mes_setup,
                         mes_batch, mes_complex_routing, mes_costing)
from api_modules.auth_deps import auth_required, admin_required

router = APIRouter(prefix="/api", tags=["Production"])


# ── Plans ──

@router.post("/plans")
async def create_plan(request: Request, user=Depends(auth_required)):
    return await mes_plan.create_plan(await request.json())


@router.get("/plans")
async def list_plans(start_date: str = None, end_date: str = None,
                     status: str = None, page: int = 1, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_plan.get_plans(start_date, end_date, status, page)


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: int, request: Request, user=Depends(auth_required)):
    return await mes_plan.get_plan_detail(plan_id)


# ── Work Orders & Results ──

@router.post("/work-orders")
async def create_work_order(request: Request, user=Depends(auth_required)):
    return await mes_work.create_work_order(await request.json())


@router.get("/work-orders")
async def list_work_orders(work_date: str = None, line_id: str = None,
                           status: str = None, request: Request = None,
                           user=Depends(auth_required)):
    return await mes_work.get_work_orders(work_date, line_id, status)


@router.get("/work-orders/{wo_id}")
async def get_work_order(wo_id: str, request: Request, user=Depends(auth_required)):
    return await mes_work.get_work_order_detail(wo_id)


@router.put("/work-orders/{wo_id}/status")
async def update_wo_status(wo_id: str, request: Request, user=Depends(auth_required)):
    return await mes_work.update_work_order_status(wo_id, await request.json())


@router.post("/work-results")
async def create_work_result(request: Request, user=Depends(auth_required)):
    return await mes_work.create_work_result(await request.json())


@router.get("/dashboard/production")
async def production_dashboard(date: str = None, request: Request = None,
                               user=Depends(auth_required)):
    return await mes_work.get_dashboard(date)


# ── Dispatch ──

@router.post("/dispatch/auto")
async def auto_dispatch_ep(request: Request, user=Depends(admin_required)):
    body = await request.json()
    return await mes_dispatch.auto_dispatch(body.get("plan_id"))


@router.post("/dispatch/backflush")
async def backflush_ep(request: Request, user=Depends(auth_required)):
    body = await request.json()
    return await mes_dispatch.backflush(body.get("wo_code", ""), body.get("good_qty", 0))


# ── Setup Matrix ──

@router.post("/setup-matrix")
async def upsert_setup_ep(request: Request, user=Depends(auth_required)):
    return await mes_setup.upsert_setup(await request.json())


@router.post("/setup-matrix/actual")
async def record_setup_actual(request: Request, user=Depends(auth_required)):
    return await mes_setup.record_actual(await request.json())


@router.get("/setup-matrix")
async def get_setup_matrix(equip_code: str = None, request: Request = None,
                           user=Depends(auth_required)):
    return await mes_setup.get_matrix(equip_code)


# ── Costing ──

@router.post("/costing")
async def add_cost_ep(request: Request, user=Depends(auth_required)):
    return await mes_costing.add_cost(await request.json())


@router.get("/costing/{wo_code}")
async def get_wo_cost_ep(wo_code: str, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_costing.get_wo_cost(wo_code)


@router.get("/costing")
async def cost_summary(request: Request = None, user=Depends(auth_required)):
    return await mes_costing.get_cost_summary()


# ── Batch ──

@router.post("/batch")
async def create_batch_ep(request: Request, user=Depends(auth_required)):
    return await mes_batch.create_batch(await request.json())


@router.get("/batch")
async def list_batch(status: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_batch.get_batches(status)


@router.put("/batch/{batch_id}/transition")
async def transition_batch_ep(batch_id: int, request: Request,
                              user=Depends(auth_required)):
    return await mes_batch.transition_batch(batch_id, await request.json())


@router.post("/batch/{batch_id}/ebr")
async def add_ebr(batch_id: int, request: Request, user=Depends(auth_required)):
    return await mes_batch.add_ebr_record(batch_id, await request.json())


@router.get("/batch/{batch_id}/ebr")
async def get_ebr_ep(batch_id: int, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_batch.get_ebr(batch_id)


# ── Complex Routing ──

@router.post("/complex-routing")
async def create_crouting(request: Request, user=Depends(admin_required)):
    return await mes_complex_routing.create_routing(await request.json())


@router.get("/complex-routing")
async def get_crouting(routing_code: str = None, item_code: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_complex_routing.get_routing(routing_code, item_code)
