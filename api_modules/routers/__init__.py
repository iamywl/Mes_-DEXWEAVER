"""APIRouter modules — NFR-010: Domain-based router separation."""

from api_modules.routers.auth import router as auth_router
from api_modules.routers.master import router as master_router
from api_modules.routers.production import router as production_router
from api_modules.routers.equipment import router as equipment_router
from api_modules.routers.quality import router as quality_router
from api_modules.routers.inventory import router as inventory_router
from api_modules.routers.ai import router as ai_router
from api_modules.routers.reports import router as reports_router
from api_modules.routers.operations import router as operations_router
from api_modules.routers.system import router as system_router

all_routers = [
    auth_router,
    master_router,
    production_router,
    equipment_router,
    quality_router,
    inventory_router,
    ai_router,
    reports_router,
    operations_router,
    system_router,
]
