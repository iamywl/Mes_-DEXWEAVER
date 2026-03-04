"""Equipment router — Equipment + OEE + CMMS + Calibration + Energy + Sensor."""

from fastapi import APIRouter, Depends, Request
from api_modules import (mes_equipment, mes_oee, mes_maintenance,
                         mes_calibration, mes_energy, mes_datacollect)
from api_modules.auth_deps import auth_required, admin_required

router = APIRouter(prefix="/api", tags=["Equipment"])


# ── Equipment ──

@router.post("/equipments")
async def create_equipment(request: Request, user=Depends(auth_required)):
    return await mes_equipment.create_equipment(await request.json())


@router.get("/equipments")
async def list_equipments(process_code: str = None, status: str = None,
                          request: Request = None, user=Depends(auth_required)):
    return await mes_equipment.get_equipments(process_code, status)


@router.put("/equipments/{equip_code}/status")
async def update_equip_status(equip_code: str, request: Request,
                              user=Depends(auth_required)):
    return await mes_equipment.update_status(equip_code, await request.json())


@router.get("/equipments/status")
async def equip_status_dashboard(request: Request, user=Depends(auth_required)):
    return await mes_equipment.get_equipment_status()


# ── OEE ──

@router.get("/equipment/oee/{equip_code}")
async def equip_oee(equip_code: str, start_date: str = None,
                    end_date: str = None, request: Request = None,
                    user=Depends(auth_required)):
    return await mes_oee.get_oee(equip_code, start_date, end_date)


@router.get("/equipment/oee/dashboard")
async def oee_dashboard(request: Request, user=Depends(auth_required)):
    return await mes_oee.get_oee_dashboard()


# ── Maintenance (CMMS) ──

@router.post("/maintenance/pm")
async def create_pm(request: Request, user=Depends(auth_required)):
    return await mes_maintenance.create_pm_schedule(await request.json())


@router.get("/maintenance/pm")
async def list_pm(equip_code: str = None, status: str = None,
                  request: Request = None, user=Depends(auth_required)):
    return await mes_maintenance.get_pm_schedules(equip_code, status)


@router.post("/maintenance/work-orders")
async def create_mwo(request: Request, user=Depends(auth_required)):
    return await mes_maintenance.create_maintenance_order(await request.json())


@router.put("/maintenance/work-orders/{mo_id}")
async def update_mwo(mo_id: str, request: Request, user=Depends(auth_required)):
    return await mes_maintenance.update_maintenance_order(mo_id, await request.json())


@router.get("/maintenance/history/{equip_code}")
async def maint_history(equip_code: str, mo_type: str = None,
                        start_date: str = None, end_date: str = None,
                        request: Request = None, user=Depends(auth_required)):
    return await mes_maintenance.get_maintenance_history(
        equip_code, mo_type, start_date, end_date)


# ── Calibration ──

@router.post("/calibration/gauges")
async def create_gauge_ep(request: Request, user=Depends(admin_required)):
    return await mes_calibration.create_gauge(await request.json())


@router.get("/calibration/gauges")
async def list_gauges(status: str = None, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_calibration.get_gauges(status)


@router.post("/calibration/gauges/{calibration_id}/records")
async def record_calib(calibration_id: int, request: Request,
                       user=Depends(auth_required)):
    return await mes_calibration.record_calibration(calibration_id, await request.json())


# ── Energy ──

@router.post("/energy")
async def record_energy_ep(request: Request, user=Depends(auth_required)):
    return await mes_energy.record_energy(await request.json())


@router.get("/energy/dashboard")
async def energy_dash(equip_code: str = None, energy_type: str = None,
                      hours: int = 24, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_energy.get_energy_dashboard(equip_code, energy_type, hours)


@router.get("/energy/per-unit")
async def energy_per_unit(request: Request = None, user=Depends(auth_required)):
    return await mes_energy.get_energy_per_unit()


# ── Sensor / DataCollect ──

@router.post("/datacollect/mqtt/config")
async def save_mqtt(request: Request, user=Depends(admin_required)):
    return await mes_datacollect.save_mqtt_config(await request.json())


@router.get("/datacollect/mqtt/config")
async def list_mqtt(request: Request = None, user=Depends(auth_required)):
    return await mes_datacollect.get_mqtt_configs()


@router.get("/datacollect/realtime/{equip_code}")
async def realtime_sensor(equip_code: str, sensor_type: str = None,
                          minutes: int = 30, interval: str = "raw",
                          request: Request = None, user=Depends(auth_required)):
    return await mes_datacollect.get_realtime_sensor(
        equip_code, sensor_type, minutes, interval)


@router.post("/datacollect/sensor")
async def insert_sensor(request: Request, user=Depends(auth_required)):
    return await mes_datacollect.insert_sensor_data(await request.json())
