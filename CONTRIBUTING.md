# Contributing

Este projeto adota um fluxo simples baseado em branches de feature e Pull Requests (PR) para a `main`.

## Convenção de nomes de branches

- Formato: `type/scope-slug[-TICKET]`
- `type`: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `hotfix`
- `scope` (curto, minúsculo): por exemplo `frontend`, `backend`, `auth`, `fin`, `infra`, `ci`, `devops`
- `slug`: resumo em kebab-case, sem acentos e sem espaços
- `TICKET` (opcional): ex. `WEB-004`, `FIN-010`, `#127`

Exemplos:
- `feat/frontend-reports-WEB-004`
- `fix/backend-transfer-tz-FIN-010`
- `chore/ci-cors-expose-request-id-127`
- `docs/readme-badge-ci-#130`
- Urgente: `hotfix/backend-auth-jwt-secret-20251103`

Regras:
- Sempre minúsculas; palavras separadas por `-` no `slug`.
- Um assunto por branch/PR (pequenos e focados).
- Crie a branch a partir de `main`: `git switch -c feat/frontend-reports-WEB-004`.

## Commits e PRs

- Prefira commits atômicos; use `git add -p` para selecionar partes relevantes.
- Título do PR pode começar pelo ticket quando houver: `WEB-004: Balance by account UI`.
- Pode fechar issue pelo corpo do PR/commit (`Closes #130`).

## Mensagens de commit (Conventional Commits)

Formato básico: `type(scope)!: assunto`

- `type`: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `revert`
- `scope` (opcional): área afetada, ex.: `frontend`, `backend`, `auth`, `fin`, `ci`
- `!` (opcional): indica breaking change
- `assunto`: frase curta no imperativo, sem ponto final

Boas práticas:
- Assunto ideal até 50 caracteres; quebre o corpo em linhas de ~72 colunas.
- Corpo (opcional): explique o “por quê”/contexto e impactos.
- Rodapé (opcional): `Closes #123`, `Refs #123`, `BREAKING CHANGE: descrição`, `Co-authored-by: Nome <email>`

Exemplos:
- `feat/frontend: relatórios de saldo por conta (WEB-004)`
- `fix/backend: occurred_at timezone-aware em transfers (FIN-010)`
- `chore/ci: expor X-Request-ID no CORS (#127)`
- `docs/readme: adiciona badge de CI`
- `refactor/auth: simplifica middleware de JWT`
- `perf/fin: otimiza consulta de relatórios`
- `test/fin: cobre casos de transfers voided`

Breaking change (duas formas válidas):
```
feat(api)!: renomeia user_id para owner_id

Atualiza schema e migrações.

BREAKING CHANGE: endpoints passam a exigir owner_id
```

## Filosofias adotadas

- TDD, DRY, KISS e YAGNI: PRs pequenos, objetivos e com testes.
- Gestão de segredos: `.env` não versionado; não inclua credenciais em commits/PRs.
- Empacotamento: use `uv` (pip é proibido neste projeto).
