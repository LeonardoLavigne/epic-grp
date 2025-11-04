import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.db.base import Base
from app.modules.finance.infrastructure.external.fx_rate_service import get_rate, RateNotFound


DB_FILE = Path("./test_fin_fx.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    if DB_FILE.exists():
        DB_FILE.unlink()
    engine = create_async_engine(TEST_DB_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    asyncio.run(init_models())

    yield async_session

    async def drop_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(drop_models())
    try:
        DB_FILE.unlink()
    except FileNotFoundError:
        pass


@pytest.mark.asyncio
async def test_get_rate_base_equals_quote(setup_db):
    async_session = setup_db
    async with async_session() as s:
        r = await get_rate(s, date=dt.date(2025, 1, 1), base="eur", quote="EUR")
        assert r == Decimal("1.0")


@pytest.mark.asyncio
async def test_get_rate_found(setup_db):
    # Insert one rate directly using ORM
    from app.modules.finance.infrastructure.persistence.models.fx_rate import FxRate

    async_session = setup_db
    async with async_session() as s:
        fx = FxRate(date=dt.date(2025, 1, 2), base="EUR", quote="BRL", rate_value=Decimal("5.1234567890"))
        s.add(fx)
        await s.commit()
        # Query
        r = await get_rate(s, date=dt.date(2025, 1, 2), base="EUR", quote="BRL")
        assert isinstance(r, Decimal)
        assert r == Decimal("5.1234567890")


@pytest.mark.asyncio
async def test_get_rate_missing_raises(setup_db):
    async_session = setup_db
    async with async_session() as s:
        with pytest.raises(RateNotFound):
            await get_rate(s, date=dt.date(2025, 1, 3), base="EUR", quote="BRL")

