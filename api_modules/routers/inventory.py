"""Inventory router — Inventory + LOT Trace."""

from fastapi import APIRouter, Depends, Request
from api_modules import mes_inventory, mes_inventory_movement, mes_lot_trace
from api_modules.auth_deps import auth_required

router = APIRouter(prefix="/api", tags=["Inventory"])


@router.post("/inventory/in")
async def inventory_in(request: Request, user=Depends(auth_required)):
    return await mes_inventory.inventory_in(await request.json())


@router.post("/inventory/out")
async def inventory_out(request: Request, user=Depends(auth_required)):
    return await mes_inventory.inventory_out(await request.json())


@router.get("/inventory")
async def get_inventory(warehouse: str = None, category: str = None,
                        request: Request = None, user=Depends(auth_required)):
    return await mes_inventory.get_inventory(warehouse, category)


@router.post("/inventory/move")
async def inventory_move(request: Request, user=Depends(auth_required)):
    body = await request.json()
    return await mes_inventory_movement.move_inventory(
        body["item_code"], body["lot_no"], body["qty"],
        body["from_location"], body["to_location"],
    )


@router.get("/lot/trace/{lot_no}")
async def lot_trace(lot_no: str, request: Request, user=Depends(auth_required)):
    return await mes_inventory.trace_lot(lot_no)


@router.get("/lot/genealogy/{lot_no}")
async def lot_genealogy(lot_no: str, direction: str = "both",
                        request: Request = None, user=Depends(auth_required)):
    return await mes_lot_trace.trace_genealogy(lot_no, direction)
