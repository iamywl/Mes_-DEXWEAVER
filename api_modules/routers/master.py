"""Master data router — Items + BOM + Process + Routings."""

from fastapi import APIRouter, Depends, Request
from api_modules import mes_items, mes_bom, mes_process
from api_modules.auth_deps import auth_required

router = APIRouter(prefix="/api", tags=["Master Data"])


# ── Items ──

@router.post("/items")
async def create_item(request: Request, user=Depends(auth_required)):
    return await mes_items.create_item(await request.json())


@router.get("/items")
async def list_items(keyword: str = None, category: str = None,
                     page: int = 1, size: int = 20, request: Request = None,
                     user=Depends(auth_required)):
    return await mes_items.get_items(keyword, category, page, size)


@router.get("/items/{item_code}")
async def get_item(item_code: str, request: Request,
                   user=Depends(auth_required)):
    return await mes_items.get_item_detail(item_code)


@router.put("/items/{item_code}")
async def update_item(item_code: str, request: Request,
                      user=Depends(auth_required)):
    return await mes_items.update_item(item_code, await request.json())


@router.delete("/items/{item_code}")
async def delete_item(item_code: str, request: Request,
                      user=Depends(auth_required)):
    return await mes_items.delete_item(item_code)


# ── BOM ──

@router.post("/bom")
async def create_bom(request: Request, user=Depends(auth_required)):
    return await mes_bom.create_bom(await request.json())


@router.get("/bom")
async def list_bom(request: Request, user=Depends(auth_required)):
    return await mes_bom.list_bom()


@router.put("/bom/{bom_id}")
async def update_bom(bom_id: int, request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.update_bom(bom_id, await request.json())


@router.delete("/bom/{bom_id}")
async def delete_bom(bom_id: int, request: Request,
                     user=Depends(auth_required)):
    return await mes_bom.delete_bom(bom_id)


@router.get("/bom/summary")
async def bom_summary(request: Request, user=Depends(auth_required)):
    return await mes_bom.bom_summary()


@router.get("/bom/where-used/{item_code}")
async def bom_where_used(item_code: str, request: Request,
                         user=Depends(auth_required)):
    return await mes_bom.where_used(item_code)


@router.get("/bom/explode/{item_code}")
async def explode_bom(item_code: str, qty: float = 1, request: Request = None,
                      user=Depends(auth_required)):
    return await mes_bom.explode_bom(item_code, qty)


# ── Process & Routing ──

@router.get("/processes")
async def list_processes(request: Request, user=Depends(auth_required)):
    return await mes_process.list_processes()


@router.post("/processes")
async def create_process(request: Request, user=Depends(auth_required)):
    return await mes_process.create_process(await request.json())


@router.put("/processes/{process_code}")
async def update_process(process_code: str, request: Request,
                         user=Depends(auth_required)):
    return await mes_process.update_process(process_code, await request.json())


@router.delete("/processes/{process_code}")
async def delete_process(process_code: str, request: Request,
                         user=Depends(auth_required)):
    return await mes_process.delete_process(process_code)


@router.get("/routings")
async def list_routings_summary(request: Request, user=Depends(auth_required)):
    return await mes_process.list_routings_summary()


@router.post("/routings")
async def create_routing(request: Request, user=Depends(auth_required)):
    return await mes_process.create_routing(await request.json())


@router.get("/routings/{item_code}")
async def get_routing(item_code: str, request: Request,
                      user=Depends(auth_required)):
    return await mes_process.get_routing(item_code)
