# epic-grp

[![CI](https://github.com/LeonardoLavigne/epic-grp/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonardoLavigne/epic-grp/actions/workflows/ci.yml)

Projeto FastAPI configurado com uv (sem pip), usando Python 3.14 (mais recente estável).

## Requisitos
- uv (gerenciador de pacotes/projetos)

## Python (3.14)
- Instalar e fixar versão (pin):

```bash
uv python install 3.14
uv python pin 3.14
```

- Conferir versões:

```bash
uv python list
```

## Inicialização do projeto
- Instalar dependências (lock + .venv gerados automaticamente):

```bash
uv sync
```

- Rodar servidor de desenvolvimento:

```bash
uv run uvicorn app.main:app --reload
```

## Dependências
As dependências estão declaradas em `pyproject.toml` e são gerenciadas com `uv`.
- Produção: FastAPI, Uvicorn, SQLAlchemy, asyncpg, Alembic, Pydantic Settings, python-dotenv, Argon2, PyJWT, python-multipart.
- Desenvolvimento: pytest, pytest-asyncio, httpx, ruff, black, mypy, pytest-cov.

### Adicionar/remover pacotes
- Adicionar pacote:

```bash
uv add <pacote>
```

- Adicionar pacotes de desenvolvimento:

```bash
uv add --dev <pacotes>
```

- Remover pacote:

```bash
uv remove <pacote>
```

- Sincronizar ambiente após mudanças:

```bash
uv sync
```

## Configuração de Ambiente
- Crie seu `.env` a partir do exemplo e ajuste os valores:

```bash
cp .env.example .env
```

- Gere um `SECRET_KEY` forte (sem pip, com uv):

```bash
UV_CACHE_DIR=.uv-cache uv run python - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
```

- Exemplo de chaves no `.env` (NÃO comitar credenciais reais):

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/DB_NAME
SECRET_KEY=<cole_o_valor_gerado_aqui>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Banco de Dados e Migrações (PostgreSQL)
- Variável de ambiente esperada:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

- Inicializar Alembic (async):

```bash
uv run alembic init -t async alembic
```

- Gerar primeira migração e aplicar:

```bash
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```

## Testes e Qualidade
- Executar testes:

```bash
uv run pytest -q
```

- Checagem de tipos (mypy):

```bash
uv run mypy app
```

- Lint/format:

```bash
uv run ruff check .
uv run black .
```

## Observações
- Este projeto não usa `pip`. Utilize sempre os comandos de projeto do `uv` (`uv init`, `uv add`, `uv sync`, `uv run`, `uv lock`, etc.).
- `uv run --no-sync` pode ser usado quando o ambiente já estiver sincronizado.

### Git hooks (pre-commit)

- O repositório inclui um hook opcional que executa `mypy` e `pytest` antes dos commits. Para habilitar:

```bash
git config core.hooksPath .githooks
```

Você pode desabilitar temporariamente com `--no-verify` em um commit, caso necessário.

## Observabilidade e Saúde
- Endpoints de saúde:
  - `GET /health`: liveness simples da aplicação.
  - `GET /ready`: readiness — executa `SELECT 1` no banco configurado; retorna 200 se OK.
- Logs de acesso:
  - Middleware registra `method`, `path`, `status`, `duration_ms` e `request_id`.
  - Se enviar `X-Request-ID` no request, o mesmo ID é propagado e retornado no header da resposta.

## Atalhos (Makefile)
Principais comandos para desenvolvimento com uv:

```bash
make python           # Instala Python 3.14 via uv
make pin              # Grava .python-version com 3.14
make install          # uv sync (deps + .venv + uv.lock)
make run              # Sobe API com reload
make test             # Roda testes
make revision m="init" # Gera migração automática
make migrate          # Sobe migrações (upgrade head)
make downgrade        # Reverte última migração
make ready            # Consulta /ready (curl)
```

## Finanças – Ciclo de Vida e Regras de Exclusão
- Regras (consistência + rastreabilidade):
  - Accounts: não deletar se em uso; use `POST /fin/accounts/{id}/close` (status=CLOSED). Listas ocultam fechadas por padrão.
  - Categories: não deletar se referenciada; use `POST /fin/categories/{id}/deactivate` (active=false) e `POST /fin/categories/merge` (mover transações src→dst). Listas ocultam inativas por padrão.
  - Transactions: prefira `POST /fin/transactions/{id}/void` (voided=true) em vez de deletar. Listas ocultam voided por padrão.
  - Transactions geradas por Transferências: são somente leitura no contexto de transações (não podem ser editadas/voidadas/deletadas individualmente). Devem ser gerenciadas via endpoints de transferência.
  - Transfers: `POST /fin/transfers/{id}/void` anula o par; as transações ligadas ficam ocultas por padrão.

- Endpoints de ciclo de vida:
  - Fechar conta: `POST /fin/accounts/{id}/close`
  - Desativar categoria: `POST /fin/categories/{id}/deactivate`
  - Unificar categorias: `POST /fin/categories/merge` (JSON: `src_category_id`, `dst_category_id`)
  - Anular transação: `POST /fin/transactions/{id}/void`
  - Anular transferência: `POST /fin/transfers/{id}/void`

- Flags nas listagens:
  - Accounts: `GET /fin/accounts?include_closed=true`
  - Categories: `GET /fin/categories?include_inactive=true`
  - Transactions: `GET /fin/transactions?include_voided=true`

### Exemplos (curl)

Criar conta e categoria:

```bash
curl -sS -X POST http://localhost:8000/fin/accounts \
  -H 'Content-Type: application/json' \
  -d '{"name":"Main","currency":"EUR"}'

curl -sS -X POST http://localhost:8000/fin/categories \
  -H 'Content-Type: application/json' \
  -d '{"name":"Salary","type":"INCOME"}'
```

Criar transação (amount em Decimal; occurred_at ISO 8601 UTC):

```bash
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
curl -sS -X POST http://localhost:8000/fin/transactions \
  -H 'Content-Type: application/json' \
  -d '{"account_id":1,"category_id":1,"amount":"10.50","occurred_at":"'$NOW'"}'
```

### DTO – Flags úteis

- `TransactionOut.from_transfer: bool` — indica se a transação foi criada a partir de uma transferência. Permite ao frontend desabilitar ações (editar/void/delete) diretamente em transações oriundas de transferências.


Listar transações com filtros de data e tipo:

```bash
curl -sS "http://localhost:8000/fin/transactions?from_date=2025-01-01T00:00:00Z&to_date=2025-01-31T23:59:59Z&type=INCOME"
```

Criar transferência (valor destino conhecido):

```bash
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
curl -sS -X POST http://localhost:8000/fin/transfers \
  -H 'Content-Type: application/json' \
  -d '{"src_account_id":1,"dst_account_id":2,"src_amount":"122.12","dst_amount":"650.00","occurred_at":"'$NOW'"}'
```

Anular transferência e transação:

```bash
curl -sS -X POST http://localhost:8000/fin/transfers/1/void
curl -sS -X POST http://localhost:8000/fin/transactions/1/void
```

Relatórios com flags:

```bash
# Saldo por conta (mês atual), incluindo contas fechadas
curl -sS "http://localhost:8000/fin/reports/balance-by-account?include_closed=true"

# Mensal por categoria, incluindo categorias inativas
curl -sS "http://localhost:8000/fin/reports/monthly-by-category?year=2025&month=1&include_inactive=true"
```
