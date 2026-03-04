"""Reports router — Reports + KPI + Dashboard Builder + Report Builder."""

from fastapi import APIRouter, Depends, Request
from api_modules import mes_reports, mes_kpi, mes_dashboard_builder, mes_report_builder
from api_modules.auth_deps import auth_required

router = APIRouter(prefix="/api", tags=["Reports"])


# ── Reports ──

@router.get("/reports/production")
async def report_production(start_date: str = None, end_date: str = None,
                            group_by: str = "day", request: Request = None,
                            user=Depends(auth_required)):
    return await mes_reports.production_report(start_date, end_date, group_by)


@router.get("/reports/quality")
async def report_quality(start_date: str = None, end_date: str = None,
                         item_code: str = None, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_reports.quality_report(start_date, end_date, item_code)


# ── KPI ──

@router.get("/kpi/fpy")
async def kpi_fpy(process_code: str = None, item_code: str = None,
                  start_date: str = None, end_date: str = None,
                  request: Request = None, user=Depends(auth_required)):
    return await mes_kpi.get_fpy(process_code, item_code, start_date, end_date)


@router.get("/kpi/maintenance/{equip_code}")
async def kpi_maintenance(equip_code: str, start_date: str = None,
                          end_date: str = None, request: Request = None,
                          user=Depends(auth_required)):
    return await mes_kpi.get_maintenance_kpi(equip_code, start_date, end_date)


# ── Dashboard Builder ──

@router.post("/dashboard-builder/layouts")
async def save_dash(request: Request, user=Depends(auth_required)):
    return await mes_dashboard_builder.save_layout(
        await request.json(), user.get("user_id", ""))


@router.get("/dashboard-builder/layouts")
async def list_dash(request: Request = None, user=Depends(auth_required)):
    return await mes_dashboard_builder.get_layouts(user.get("user_id", ""))


@router.get("/dashboard-builder/layouts/{layout_id}")
async def detail_dash(layout_id: int, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_dashboard_builder.get_layout_detail(layout_id)


@router.delete("/dashboard-builder/layouts/{layout_id}")
async def delete_dash(layout_id: int, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_dashboard_builder.delete_layout(layout_id, user.get("user_id", ""))


# ── Report Builder ──

@router.post("/report-builder/templates")
async def create_rpt(request: Request, user=Depends(auth_required)):
    return await mes_report_builder.create_template(
        await request.json(), user.get("user_id", ""))


@router.get("/report-builder/templates")
async def list_rpt(request: Request = None, user=Depends(auth_required)):
    return await mes_report_builder.get_templates()


@router.post("/report-builder/templates/{template_id}/execute")
async def exec_rpt(template_id: int, request: Request,
                   user=Depends(auth_required)):
    return await mes_report_builder.execute_report(template_id)
