APP-001: Setup do Projeto e Estrutura Inicial
├── Subtask: Configurar repositório Git
├── Subtask: Setup inicial com uv
├── Subtask: Instalar dependências básicas (fastapi, sqlalchemy, etc.)
├── Subtask: Configurar estrutura de diretórios
├── Subtask: Setup básico do FastAPI
└── Subtask: Configuração inicial do banco PostgreSQL

APP-002: Configuração do Banco de Dados
├── Subtask: Setup SQLAlchemy
├── Subtask: Configurar Alembic para migrações
├── Subtask: Criar modelos base (User, BaseModel)
└── Subtask: Primeira migração

APP-003: Autenticação Básica
├── Subtask: Modelo User com campos básicos
├── Subtask: Hash de senha com Argon2
├── Subtask: Endpoints de registro/login
├── Subtask: JWT simples para autenticação
└── Subtask: Middleware de autenticação

APP-004: Estrutura de Dados Base
├── Subtask: Models base para todos os módulos
├── Subtask: Pydantic schemas básicos
└── Subtask: CRUD genérico

APP-005: Documentação e Testes
├── Subtask: Configurar pytest
├── Subtask: Testes básicos de autenticação
├── Subtask: Documentação automática FastAPI
└── Subtask: README com setup

FIN-001: Modelagem de Domínio (Finanças)
├── Subtask: Definir entidades Account, Category, Transaction
├── Subtask: Definir enums (TransactionType: INCOME|EXPENSE)
├── Subtask: Currency padrão em Account (EUR)
└── Subtask: Precisão monetária (Decimal na API, quantize; persistir amount_cents)

FIN-002: Migrações (Finanças)
├── Subtask: Criar tables accounts, categories, transactions
├── Subtask: Constraints e índices (unique e filtros por user_id)
└── Subtask: occurred_at UTC e audit (created_at/updated_at)

FIN-003: Schemas + Validações (Finanças)
├── Subtask: Pydantic Create/Update/Out para Account/Category/Transaction
├── Subtask: Validador Decimal (quantize por moeda; rejeitar precisão inválida)
└── Subtask: Paginação básica (skip/limit)

FIN-004: CRUD + Regras (Finanças)
├── Subtask: CRUD assíncrono filtrado por current_user.id
├── Subtask: Conversão amount (Decimal) → amount_cents (int) na persistência
└── Subtask: Herança de currency via Account (sem currency em Transaction por ora)

FIN-005: Endpoints (Finanças)
├── Subtask: Accounts (list/create/update/delete; filtro por nome)
├── Subtask: Categories (list/create/update/delete; filtro por type)
└── Subtask: Transactions (list/create/update/delete; filtros: data, account, category, type)

FIN-006: Relatórios mínimos (Finanças)
├── Subtask: GET /fin/reports/balance-by-account (INCOME +, EXPENSE -)
└── Subtask: GET /fin/reports/monthly-by-category?year=&month=

FIN-007: Testes (TDD) (Finanças)
├── Subtask: Cobertura de validações (Decimal/precisão, datas)
├── Subtask: Isolamento por usuário (scoping)
└── Subtask: Filtros e relatórios

FIN-008: Base para multi-moeda futura (Finanças)
└── Subtask: Util para mapping de exponent por currency (ISO 4217) (sem implementar lógica por transação agora)

FIN-009: Multi-moeda — Modelagem + Migrações
├── Subtask: Adicionar `currency` em `transactions` (default da `account` na criação)
├── Subtask: Criar `fx_rates(base, quote, rate, date)` com UNIQUE(base, quote, date)
└── Subtask: Índices em `(base, quote, date)`

FIN-010: Multi-moeda — Schemas + Validações
├── Subtask: `TransactionCreate/Update` aceitar `currency` opcional (usa `account.currency` se ausente)
├── Subtask: Validar precisão por moeda via `money.py` (ISO 4217)
└── Subtask: Schemas `FXRateCreate` e consulta

FIN-011: Multi-moeda — CRUD + Endpoints de FX
├── Subtask: `POST /fin/fx-rates` (criar/atualizar taxa do dia)
├── Subtask: `GET /fin/fx-rates?base=&quote=&from=&to=`
└── Subtask: Serviço `get_rate(date, base, quote)` (base==quote → 1.0)

FIN-012: Multi-moeda — Transações
├── Subtask: Persistir `amount_cents` conforme `transaction.currency`
└── Subtask: Listagem exibir `amount` + `currency` da transação (sem conversão por padrão)

FIN-013: Multi-moeda — Relatórios
├── Subtask: `report_currency` opcional; converter por `occurred_at`
├── Subtask: Falta de taxa → 422 (ou fallback se aprovado)
└── Subtask: Arredondamento por exponent da `report_currency`

FIN-014: Multi-moeda — Transferências (futuro)
├── Subtask: Duas transações ligadas por `transfer_id`
├── Subtask: Diferença FX (P&L) — posterior
└── Subtask: Fora do corte inicial
