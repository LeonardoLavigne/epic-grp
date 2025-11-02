.PHONY: help python pin install run test revision migrate downgrade ready

PY ?= 3.14

help:
	@echo "Targets:"
	@echo "  make python     # Install Python $(PY) via uv"
	@echo "  make pin        # Pin Python $(PY) to .python-version"
	@echo "  make install    # Sync deps (.venv + uv.lock)"
	@echo "  make run        # Run API dev server"
	@echo "  make test       # Run tests"
	@echo "  make revision m=msg  # Alembic autogenerate"
	@echo "  make migrate    # Alembic upgrade head"
	@echo "  make downgrade  # Alembic downgrade -1"
	@echo "  make ready      # Hit /ready endpoint"

python:
	uv python install $(PY)

pin:
	uv python pin $(PY)

install:
	uv sync --all-extras

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -q

revision:
	uv run alembic revision --autogenerate -m "$(m)"

migrate:
	uv run alembic upgrade head

downgrade:
	uv run alembic downgrade -1

ready:
	@echo "GET http://localhost:8000/ready" && curl -sS http://localhost:8000/ready | jq . || true

