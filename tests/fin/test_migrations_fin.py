import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command


TEST_DB = Path("test_fin.db")
SQLITE_ASYNC_URL = f"sqlite+aiosqlite:///{TEST_DB}"
SQLITE_SYNC_URL = f"sqlite:///{TEST_DB}"


@pytest.fixture(scope="session", autouse=True)
def run_migrations_on_sqlite():
    # Ensure a clean database file
    if TEST_DB.exists():
        TEST_DB.unlink()

    # Point Alembic to SQLite (async) via env var used in alembic/env.py
    old_env = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = SQLITE_ASYNC_URL

    try:
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        yield
    finally:
        # Downgrade back to base and cleanup DB file
        try:
            cfg = Config("alembic.ini")
            command.downgrade(cfg, "base")
        except Exception:
            pass
        if old_env is not None:
            os.environ["DATABASE_URL"] = old_env
        else:
            os.environ.pop("DATABASE_URL", None)
        try:
            TEST_DB.unlink()
        except FileNotFoundError:
            pass


def get_inspector():
    eng = create_engine(SQLITE_SYNC_URL)
    return inspect(eng)


def test_accounts_table_schema():
    insp = get_inspector()
    assert "accounts" in insp.get_table_names()
    cols = {c["name"]: c for c in insp.get_columns("accounts")}
    for required in ("id", "user_id", "name", "currency", "created_at", "updated_at"):
        assert required in cols

    uniques = insp.get_unique_constraints("accounts")
    # Expect a unique constraint on (user_id, name)
    assert any(set(u.get("column_names", [])) == {"user_id", "name"} for u in uniques)


def test_categories_table_schema():
    insp = get_inspector()
    assert "categories" in insp.get_table_names()
    cols = {c["name"]: c for c in insp.get_columns("categories")}
    for required in ("id", "user_id", "name", "type", "created_at", "updated_at"):
        assert required in cols

    uniques = insp.get_unique_constraints("categories")
    assert any(set(u.get("column_names", [])) == {"user_id", "name", "type"} for u in uniques)


def test_transactions_table_schema_and_indexes():
    insp = get_inspector()
    assert "transactions" in insp.get_table_names()

    cols = {c["name"]: c for c in insp.get_columns("transactions")}
    for required in (
        "id",
        "user_id",
        "account_id",
        "category_id",
        "amount_cents",
        "occurred_at",
        "description",
        "created_at",
        "updated_at",
    ):
        assert required in cols

    # Foreign keys presence
    fks = insp.get_foreign_keys("transactions")
    fk_cols = {fk.get("constrained_columns")[0]: fk.get("referred_table") for fk in fks}
    assert fk_cols.get("account_id") == "accounts"
    # category_id is optional but FK should exist to categories
    assert fk_cols.get("category_id") == "categories"

    # Indexes for performance/filters
    idx = insp.get_indexes("transactions")
    cols_sets = [set(i.get("column_names", [])) for i in idx]
    assert {"user_id", "occurred_at"} in cols_sets
    assert {"user_id", "account_id"} in cols_sets
    assert {"user_id", "category_id"} in cols_sets

