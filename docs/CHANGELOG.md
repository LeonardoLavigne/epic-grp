# Changelog

All notable changes to this project are documented in this file.
This project follows a simplified Keep a Changelog style and Conventional Commits for messages.

## [Unreleased]
- Reports: Multi‑currency totals in Monthly by Category (FIN‑010).
- Frontend: dedicated view/route for transfer details (besides the inline panel).

## [0.1.0] – 2025-11-03

### Added
- Backend
  - Finance domain (WEB‑003):
    - Accounts: list/create/close; filter closed on demand.
    - Categories: list/create/deactivate/merge; type filter.
    - Transactions: list (filters: date/account/category/type), create, void.
    - Transfers: create (dst_amount or fx_rate), GET by id, void (pair).
    - Domain rules: amounts stored as cents per currency exponent; UTC datetimes.
  - Reports (WEB‑004):
    - Balance by Account (filters: year/month/include_closed).
    - Monthly by Category (filters: year/month/include_closed/include_inactive).
  - Observability/Health:
    - Endpoints: `GET /health`, `GET /ready` (DB readiness check).
    - Request ID propagation with `X-Request-ID` in responses and logs.
  - Auth: minimal register/login flow with JWT (PyJWT) and Settings via .env.
  - Alembic configured; migrations for users/finances.
  - CORS configured; `X-Request-ID` exposed for frontend.

- Frontend
  - Base stack: Vite + React + TypeScript + Tailwind.
  - Pages (WEB‑003, WEB‑004, WEB‑005):
    - Auth: Login/Register.
    - Finances: Accounts, Categories, Transactions, Transfers.
    - Reports: Balance by Account, Monthly by Category (CSV export, filters).
    - Observability: `/ready` indicator and `ReqID` display+copy.
  - Interceptors Axios: captura segura de `X-Request-ID` e skip para `/ready`.
  - UI components: Button, Card, MoneyInput (Decimal), DateTimeISO (UTC), MonthYearPicker, Toaster.
  - UX guards em transações:
    - `from_transfer` flag e `transfer_id` no DTO; oculta "Void" quando `from_transfer=true`.
    - Ação "Ver transferência" abre painel com detalhes.

- DX/Tooling
  - Gerenciado com `uv` (Python 3.14); Makefile com atalhos.
  - CI com badge; lint/format/tests via `uv run`.
  - `CONTRIBUTING.md`: convenção de branches e Conventional Commits.
  - `scripts/fin_diag.py`: diagnóstico de saldos/transações por mês/usuário.

### Changed
- Reports
  - Balance by Account: passa a incluir transações de categorias inativas (categoria é rótulo; saldo deve considerar a transação). Exclui `voided` por padrão.
  - Monthly by Category: exclui `voided` por padrão; mantém filtro por `include_inactive` para o relatório por categoria.
- Transfers
  - `occurred_at` timezone‑aware (UTC); coerção consistente.
  - Categorias de sistema "Transfer In/Out": auto‑reativadas se encontradas inativas ao criar transfer.
- Observabilidade
  - Interceptor não sobrescreve ReqID com `/ready` (header `X-Skip-ReqID-Capture`).

### Fixed
- Impede editar/void/deletar transações ligadas a transferências (409). Operações devem ser feitas via endpoints de `transfers`.
- Saldo incorreto quando categorias de transferência estavam inativas.
- Relatórios contavam transações voided — agora excluídas por padrão.
- Diversos ajustes menores em CORS e captura de headers para compatibilidade de navegadores.

### Security
- Gestão de segredos via `.env` (não versionado); JWT `SECRET_KEY` requerido no startup.

[Unreleased]: https://github.com/LeonardoLavigne/epic-grp/compare/main...HEAD
[0.1.0]: https://github.com/LeonardoLavigne/epic-grp/compare/initial...0.1.0

