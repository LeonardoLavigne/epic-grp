from typing import Callable, Awaitable
from fastapi import Depends, HTTPException, status

from app.core.settings import get_settings, Settings
from app.core.auth.persistence.models.user import User
from app.core.auth.security import get_current_user


def require_module(module: str) -> Callable[..., Awaitable[None]]:
    async def _dep(
        current_user: User = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
    ) -> None:
        # Global flags first (KISS). Future: check entitlements for the user here.
        if module == "finance" and not getattr(settings, "enable_finance", True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module 'finance' disabled")
        if module == "health" and not getattr(settings, "enable_health", False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module 'health' disabled")

    return _dep
