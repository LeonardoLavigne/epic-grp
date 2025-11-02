from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.settings import get_settings, Settings
from app.crud.user import get_user_by_email, create_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = await get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(session, user_in.email, user_in.password)
    return user


@router.post("/login", response_model=Token)
async def login(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_by_email(session, user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.email}, settings)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def read_me(current_user=Depends(get_current_user)):
    return current_user

