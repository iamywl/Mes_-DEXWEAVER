"""Quality router — Quality + SPC + CAPA + NCR + Disposition + MSA + FMEA + Barcode."""

from fastapi import APIRouter, Depends, Request
from api_modules import (mes_quality, mes_spc, mes_capa, mes_ncr,
                         mes_disposition, mes_msa, mes_fmea, mes_barcode)
from api_modules.auth_deps import auth_required

router = APIRouter(prefix="/api", tags=["Quality"])


# ── Quality Standards & Inspections ──

@router.post("/quality/standards")
async def create_quality_standard(request: Request, user=Depends(auth_required)):
    return await mes_quality.create_standard(await request.json())


@router.post("/quality/inspections")
async def create_inspection(request: Request, user=Depends(auth_required)):
    return await mes_quality.create_inspection(await request.json())


@router.get("/quality/defects")
async def get_defects(start_date: str = None, end_date: str = None,
                      item_code: str = None, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_quality.get_defects(start_date, end_date, item_code)


# ── SPC ──

@router.get("/quality/spc/{item_code}")
async def spc_chart(item_code: str, check_name: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_spc.get_spc_chart(item_code, check_name)


@router.post("/quality/spc/rules")
async def create_spc_rule(request: Request, user=Depends(auth_required)):
    return await mes_spc.create_spc_rule(await request.json())


@router.get("/quality/cpk/{item_code}")
async def cpk_analysis(item_code: str, check_name: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_spc.get_cpk(item_code, check_name)


@router.post("/quality/spc/auto-actions")
async def spc_auto_act(request: Request, user=Depends(auth_required)):
    return await mes_spc.spc_auto_actions(await request.json())


# ── CAPA ──

@router.post("/quality/capa")
async def create_capa(request: Request, user=Depends(auth_required)):
    return await mes_capa.create_capa(await request.json())


@router.put("/quality/capa/{capa_id}/status")
async def update_capa_status(capa_id: str, request: Request,
                             user=Depends(auth_required)):
    return await mes_capa.update_capa_status(capa_id, await request.json())


@router.get("/quality/capa")
async def list_capa(status: str = None, capa_type: str = None,
                    assigned_to: str = None, request: Request = None,
                    user=Depends(auth_required)):
    return await mes_capa.get_capa_list(status, capa_type, assigned_to)


# ── NCR ──

@router.post("/quality/ncr")
async def create_ncr(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_ncr.create_ncr(await request.json(), user_id)


@router.get("/quality/ncr")
async def list_ncr(status: str = None, lot_no: str = None,
                   request: Request = None, user=Depends(auth_required)):
    return await mes_ncr.get_ncr_list(status, lot_no)


@router.put("/quality/ncr/{ncr_id}/disposition")
async def ncr_disposition(ncr_id: str, request: Request,
                          user=Depends(auth_required)):
    return await mes_ncr.update_ncr_disposition(ncr_id, await request.json())


# ── Disposition ──

@router.post("/quality/disposition")
async def create_disp(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_disposition.create_disposition(await request.json(), user_id)


@router.get("/quality/disposition")
async def list_disp(lot_no: str = None, decision: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_disposition.get_dispositions(lot_no, decision)


# ── MSA ──

@router.post("/msa/studies")
async def create_msa(request: Request, user=Depends(auth_required)):
    return await mes_msa.create_study(await request.json())


@router.get("/msa/studies")
async def get_msa_list(gauge_code: str = None, study_type: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_msa.get_studies(gauge_code, study_type)


@router.post("/msa/studies/{study_id}/measurements")
async def add_msa_meas(study_id: int, request: Request, user=Depends(auth_required)):
    return await mes_msa.add_measurements(study_id, await request.json())


@router.post("/msa/studies/{study_id}/calculate")
async def calc_grr(study_id: int, request: Request, user=Depends(auth_required)):
    return await mes_msa.calculate_grr(study_id)


# ── FMEA ──

@router.post("/fmea")
async def create_fmea_doc(request: Request, user=Depends(auth_required)):
    return await mes_fmea.create_fmea(await request.json())


@router.get("/fmea")
async def list_fmea(item_code: str = None, status: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_fmea.get_fmea_list(item_code, status)


@router.get("/fmea/{fmea_id}")
async def detail_fmea(fmea_id: int, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_fmea.get_fmea_detail(fmea_id)


@router.post("/fmea/{fmea_id}/items")
async def add_fmea_item_ep(fmea_id: int, request: Request,
                           user=Depends(auth_required)):
    return await mes_fmea.add_fmea_item(fmea_id, await request.json())


# ── Barcode ──

@router.post("/barcode/generate")
async def barcode_generate(request: Request, user=Depends(auth_required)):
    return await mes_barcode.generate_barcode(await request.json())


@router.post("/barcode/scan")
async def barcode_scan(request: Request, user=Depends(auth_required)):
    return await mes_barcode.scan_barcode(await request.json())
