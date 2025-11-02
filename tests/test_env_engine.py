import os
import importlib
from pathlib import Path

from sqlalchemy.engine import make_url


def test_engine_uses_env_var(monkeypatch):
    # Arrange: set an explicit DATABASE_URL and reload the module
    from app.db import session as db_session  # import for reload target

    db_url = "postgresql+asyncpg://u:p@host:5432/db1"
    monkeypatch.setenv("DATABASE_URL", db_url)

    importlib.reload(db_session)

    # Act: create the engine lazily
    db_session._ensure_engine()  # type: ignore[attr-defined]

    # Assert: engine uses the env-provided URL (no connection attempted)
    actual = db_session._engine.sync_engine.url  # type: ignore[attr-defined]
    expected = make_url(db_url)
    assert actual.drivername == expected.drivername
    assert actual.username == expected.username
    assert actual.host == expected.host
    assert actual.database == expected.database


def test_startup_loads_env_file(monkeypatch, tmp_path: Path):
    # Arrange: ensure no env vars and prepare a .env with SECRET_KEY + DATABASE_URL
    for key in ("DATABASE_URL", "SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES"):
        monkeypatch.delenv(key, raising=False)

    env_path = Path(".env")
    existed = env_path.exists()
    original = env_path.read_text() if existed else None

    db_url = "postgresql+asyncpg://user:pass@localhost:5432/example"
    env_content = (
        f"DATABASE_URL={db_url}\n"
        "SECRET_KEY=test-secret-from-env-file\n"
        "ALGORITHM=HS256\nACCESS_TOKEN_EXPIRE_MINUTES=60\n"
    )
    env_path.write_text(env_content)

    # Import app and trigger startup (which calls load_dotenv())
    from app.main import create_app
    from fastapi.testclient import TestClient
    from app.db import session as db_session

    try:
        importlib.reload(db_session)  # reset lazy engine state
        with TestClient(create_app()):
            pass  # triggers startup event

        # Act: create engine after startup
        db_session._ensure_engine()  # type: ignore[attr-defined]

        # Assert URL comes from .env
        actual = db_session._engine.sync_engine.url  # type: ignore[attr-defined]
        expected = make_url(db_url)
        assert actual.drivername == expected.drivername
        assert actual.username == expected.username
        assert actual.host == expected.host
        assert actual.database == expected.database
    finally:
        # Restore user's .env if it existed; otherwise remove the file we created
        if existed:
            assert original is not None
            env_path.write_text(original)
        else:
            try:
                env_path.unlink()
            except FileNotFoundError:
                pass
