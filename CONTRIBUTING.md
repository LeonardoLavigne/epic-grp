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

## Filosofias adotadas

- TDD, DRY, KISS e YAGNI: PRs pequenos, objetivos e com testes.
- Gestão de segredos: `.env` não versionado; não inclua credenciais em commits/PRs.
- Empacotamento: use `uv` (pip é proibido neste projeto).

