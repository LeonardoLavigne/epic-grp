from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from sqlalchemy.engine import make_url
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.api.routes.auth import router as auth_router
from app.api.routes.finance import router as fin_router
from app.core.security import get_current_user
from app.schemas.user import UserOut
from app.core.settings import get_settings
from app.middleware.access_log import AccessLogMiddleware


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load .env into process env
        load_dotenv()

        # Fail fast if required settings (e.g., SECRET_KEY) are missing/invalid
        s = get_settings()
        logging.getLogger("uvicorn").info(
            "Settings loaded (algorithm=%s, access_token_expire_minutes=%s)",
            s.algorithm,
            s.access_token_expire_minutes,
        )

        # Minimal DATABASE_URL validation + warnings (no secrets in logs)
        db_url = os.getenv("DATABASE_URL")
        logger = logging.getLogger("uvicorn")
        if not db_url:
            logger.warning(
                "DATABASE_URL is not set; using default local URL from app.db.session."
            )
        else:
            try:
                url = make_url(db_url)
                if not url.drivername.startswith("postgresql"):
                    logger.warning(
                        "DATABASE_URL driver '%s' is not PostgreSQL; check configuration.",
                        url.drivername,
                    )
            except Exception:
                logger.warning("DATABASE_URL has an invalid format; check configuration.")

        yield

    app = FastAPI(title="epic-grp", lifespan=lifespan)
    app.add_middleware(AccessLogMiddleware)

    # CORS (dev-friendly by default; configurable via CORS_ORIGINS)
    origins_env = os.getenv("CORS_ORIGINS", "")
    if origins_env:
        allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    else:
        allow_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(fin_router)

    @app.get("/me", response_model=UserOut)
    async def me(current_user=Depends(get_current_user)):
        return current_user

    # Readiness endpoint: checks DB connectivity
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import get_session

    @app.get("/ready")
    async def ready(session: AsyncSession = Depends(get_session)):
        await session.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
