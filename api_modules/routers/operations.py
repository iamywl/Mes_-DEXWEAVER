"""Operations router — Notification + EWI + Recipe + DMS + Labor + ERP + OPC-UA + Audit + ECM + SQM + Multisite."""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from api_modules import (mes_notification, mes_auth, mes_ewi, mes_recipe,
                         mes_document, mes_labor, mes_erp, mes_opcua,
                         mes_audit, mes_i18n, mes_resource, mes_ecm,
                         mes_sqm, mes_multisite)
from api_modules.auth_deps import auth_required, admin_required

router = APIRouter(prefix="/api", tags=["Operations"])


# ── Notifications ──

@router.get("/notifications")
async def list_notifications(unread_only: bool = False, limit: int = 50,
                             request: Request = None, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_notification.get_notifications(user_id, unread_only, limit)


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, request: Request,
                                  user=Depends(auth_required)):
    return await mes_notification.mark_read(notification_id)


@router.get("/notifications/settings")
async def get_notif_settings(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_notification.get_notification_settings(user_id)


@router.post("/notifications/settings")
async def update_notif_settings(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_notification.update_notification_settings(user_id, await request.json())


# ── EWI ──

@router.post("/work-instructions")
async def create_wi(request: Request, user=Depends(auth_required)):
    return await mes_ewi.create_work_instruction(await request.json())


@router.get("/work-instructions")
async def list_wi(wo_no: str = None, status: str = None,
                  request: Request = None, user=Depends(auth_required)):
    return await mes_ewi.get_work_instructions(wo_no, status)


@router.get("/work-instructions/{wi_id}")
async def get_wi(wi_id: str, request: Request = None, user=Depends(auth_required)):
    return await mes_ewi.get_work_instruction_detail(wi_id)


@router.post("/work-instructions/{wi_id}/steps/{step_no}/sign")
async def sign_wi_step(wi_id: str, step_no: int, request: Request,
                       user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_ewi.sign_step(wi_id, step_no, user_id)


# ── Recipe ──

@router.post("/recipes")
async def create_recipe(request: Request, user=Depends(auth_required)):
    return await mes_recipe.create_recipe(await request.json())


@router.get("/recipes")
async def list_recipes(item_code: str = None, process_code: str = None,
                       status: str = None, request: Request = None,
                       user=Depends(auth_required)):
    return await mes_recipe.get_recipes(item_code, process_code, status)


@router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: int, compare_version: int = None,
                     request: Request = None, user=Depends(auth_required)):
    return await mes_recipe.get_recipe_detail(recipe_id, compare_version)


@router.put("/recipes/{recipe_id}/approve")
async def approve_recipe(recipe_id: int, request: Request,
                         user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_recipe.approve_recipe(recipe_id, user_id)


# ── DMS ──

@router.post("/documents")
async def create_doc(request: Request, user=Depends(auth_required)):
    user_id = user.get("user_id", "") if isinstance(user, dict) else ""
    return await mes_document.create_document(await request.json(), user_id)


@router.get("/documents")
async def list_docs(doc_type: str = None, item_code: str = None,
                    process_code: str = None, keyword: str = None,
                    status: str = None, request: Request = None,
                    user=Depends(auth_required)):
    return await mes_document.get_documents(
        doc_type, item_code, process_code, keyword, status)


@router.put("/documents/{doc_id}/approve")
async def approve_doc(doc_id: int, request: Request, user=Depends(admin_required)):
    return await mes_document.approve_document(doc_id)


# ── Labor ──

@router.get("/labor/skills")
async def get_skills(process_code: str = None, skill_level: str = None,
                     worker_id: str = None, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_labor.get_worker_skills(process_code, skill_level, worker_id)


@router.post("/labor/skills")
async def upsert_skill(request: Request, user=Depends(admin_required)):
    return await mes_labor.upsert_worker_skill(await request.json())


# ── ERP ──

@router.post("/erp/sync-config")
async def create_erp_sync(request: Request, user=Depends(admin_required)):
    return await mes_erp.create_sync_config(await request.json())


@router.get("/erp/sync-config")
async def get_erp_syncs(request: Request = None, user=Depends(auth_required)):
    return await mes_erp.get_sync_configs()


@router.post("/erp/sync/{config_id}/execute")
async def execute_erp_sync(config_id: int, request: Request,
                           user=Depends(admin_required)):
    return await mes_erp.execute_sync(config_id, user.get("user_id", "system"))


@router.get("/erp/sync-logs")
async def get_erp_logs(config_id: int = None, status: str = None,
                       request: Request = None, user=Depends(auth_required)):
    return await mes_erp.get_sync_logs(config_id, status)


# ── OPC-UA ──

@router.post("/opcua/config")
async def create_opcua_cfg(request: Request, user=Depends(admin_required)):
    return await mes_opcua.save_opcua_config(await request.json())


@router.get("/opcua/config")
async def get_opcua_cfgs(request: Request = None, user=Depends(auth_required)):
    return await mes_opcua.get_opcua_configs()


@router.get("/opcua/status")
async def opcua_status(request: Request = None, user=Depends(auth_required)):
    return await mes_opcua.get_opcua_status()


# ── Audit ──

@router.get("/audit")
async def get_audits(entity_type: str = None, entity_id: str = None,
                     user_id: str = None, action: str = None,
                     date_from: str = None, date_to: str = None,
                     page: int = 1, page_size: int = 50,
                     request: Request = None, user=Depends(admin_required)):
    return await mes_audit.get_audit_logs(
        entity_type, entity_id, user_id, action, date_from, date_to, page, page_size)


@router.get("/audit/summary")
async def audit_summary(request: Request = None, user=Depends(admin_required)):
    return await mes_audit.get_audit_summary()


# ── i18n ──

@router.get("/i18n/translations")
async def get_i18n(locale: str = None, request: Request = None,
                   user=Depends(auth_required)):
    return await mes_i18n.get_translations(locale)


@router.get("/i18n/locales")
async def get_locales(request: Request = None, user=Depends(auth_required)):
    return await mes_i18n.get_supported_locales()


@router.post("/i18n/translations")
async def upsert_i18n(request: Request, user=Depends(admin_required)):
    return await mes_i18n.upsert_translation(await request.json())


@router.delete("/i18n/translations/{locale}/{msg_key}")
async def delete_i18n(locale: str, msg_key: str, request: Request,
                      user=Depends(admin_required)):
    return await mes_i18n.delete_translation(locale, msg_key)


# ── Resource ──

@router.get("/resources")
async def get_res(resource_type: str = None, status: str = None,
                  keyword: str = None, request: Request = None,
                  user=Depends(auth_required)):
    return await mes_resource.get_resources(resource_type, status, keyword)


@router.post("/resources")
async def create_res(request: Request, user=Depends(admin_required)):
    return await mes_resource.create_resource(await request.json())


@router.put("/resources/{resource_id}/status")
async def update_res_status(resource_id: int, request: Request,
                            user=Depends(admin_required)):
    return await mes_resource.update_resource_status(resource_id, await request.json())


@router.get("/resources/summary")
async def res_summary(request: Request = None, user=Depends(auth_required)):
    return await mes_resource.get_resource_summary()


# ── ECM ──

@router.post("/ecm")
async def create_ecr_ep(request: Request, user=Depends(auth_required)):
    return await mes_ecm.create_ecr(await request.json())


@router.get("/ecm")
async def list_ecr(status: str = None, change_type: str = None,
                   request: Request = None, user=Depends(auth_required)):
    return await mes_ecm.get_ecr_list(status, change_type)


@router.put("/ecm/{ecr_id}/transition")
async def transition_ecr_ep(ecr_id: int, request: Request,
                            user=Depends(admin_required)):
    return await mes_ecm.transition_ecr(ecr_id, await request.json())


# ── SQM ──

@router.post("/sqm/suppliers")
async def create_supplier_ep(request: Request, user=Depends(admin_required)):
    return await mes_sqm.create_supplier(await request.json())


@router.get("/sqm/suppliers")
async def list_suppliers(asl_status: str = None, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_sqm.get_suppliers(asl_status)


@router.post("/sqm/scar")
async def create_scar_ep(request: Request, user=Depends(auth_required)):
    return await mes_sqm.create_scar(await request.json())


@router.get("/sqm/scar")
async def list_scar(supplier_id: int = None, status: str = None,
                    request: Request = None, user=Depends(auth_required)):
    return await mes_sqm.get_scars(supplier_id, status)


@router.post("/sqm/suppliers/{supplier_id}/score")
async def update_score(supplier_id: int, request: Request,
                       user=Depends(admin_required)):
    return await mes_sqm.update_supplier_score(supplier_id)


# ── Multisite ──

@router.post("/sites")
async def create_site_ep(request: Request, user=Depends(admin_required)):
    return await mes_multisite.create_site(await request.json())


@router.get("/sites")
async def list_sites(request: Request = None, user=Depends(auth_required)):
    return await mes_multisite.get_sites()


@router.get("/sites/{site_id}/dashboard")
async def site_dashboard(site_id: int, request: Request = None,
                         user=Depends(auth_required)):
    return await mes_multisite.get_site_dashboard(site_id)
