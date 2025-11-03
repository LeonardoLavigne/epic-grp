from .accounts import router as accounts_router
from .categories import router as categories_router
from .transactions import router as transactions_router
from .transfers import router as transfers_router
from .reports import router as reports_router
from .fx_rates import router as fx_rates_router

__all__ = [
    "accounts_router",
    "categories_router",
    "transactions_router",
    "transfers_router",
    "reports_router",
    "fx_rates_router",
]
