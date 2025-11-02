import asyncio
import pytest
import pytest_asyncio
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models.base import Base
from app.models.user import User
from app.crud.base import CRUDBase


TEST_DB_URL = "sqlite+aiosqlite:///./test_crud.db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DB_URL, future=True)


@pytest.fixture(scope="session", autouse=True)
def setup_db(engine):
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_models())
    yield

    async def drop_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(drop_models())


@pytest_asyncio.fixture()
async def session(engine):
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as s:  # type: AsyncSession
        yield s


class UserCreateRaw(BaseModel):
    email: EmailStr
    hashed_password: str


class UserUpdateEmail(BaseModel):
    email: EmailStr


@pytest.mark.asyncio
async def test_crud_base_user(session: AsyncSession):
    crud_user = CRUDBase[User, UserCreateRaw, UserUpdateEmail](User)

    # create
    created = await crud_user.create(
        session, UserCreateRaw(email="crud@example.com", hashed_password="plainhash")
    )
    assert created.id is not None
    assert created.email == "crud@example.com"

    # get
    fetched = await crud_user.get(session, created.id)
    assert fetched is not None and fetched.email == created.email

    # get_multi
    items = await crud_user.get_multi(session, skip=0, limit=10)
    assert any(u.email == "crud@example.com" for u in items)

    # update
    updated = await crud_user.update(
        session, fetched, UserUpdateEmail(email="crud2@example.com")
    )
    assert updated.email == "crud2@example.com"

    # remove
    removed = await crud_user.remove(session, updated.id)
    assert removed is not None and removed.id == updated.id
    missing = await crud_user.get(session, updated.id)
    assert missing is None
