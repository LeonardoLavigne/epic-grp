import os
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


_DEFAULT_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
_engine = None
_SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def _ensure_engine() -> None:
    global _engine, _SessionLocal
    if _engine is None:
        url = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
        _engine = create_async_engine(url, echo=False, future=True)
        _SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    if _SessionLocal is None:
        _ensure_engine()
    assert _SessionLocal is not None  # for type checkers
    async with _SessionLocal() as session:
        yield session
