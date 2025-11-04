# Plano de Correção do Módulo Finance

## 1. Problemas Identificados

1. Árvores `domain/entities` e `infrastructure/persistence/models` duplicam os mesmos modelos ORM (ex.: [`Account`](app/modules/finance/domain/entities/account.py), [`Account`](app/modules/finance/infrastructure/persistence/models/account.py)), violando a separação entre domínio e infraestrutura.
2. Código de aplicação (`CreateTransferUseCase`, [`GenerateReportsUseCase`](app/modules/finance/application/use_cases/generate_reports.py)) depende diretamente de `app.models.finance.*`, que deixou de existir após a refatoração.
3. Persistência (ex.: [`category.py`](app/modules/finance/infrastructure/persistence/category.py)) mistura modelos da camada antiga (`app.models.finance.Category`) com os novos modelos.
4. Interfaces de API continuam acopladas aos modelos antigos, por exemplo [`transactions.py`](app/modules/finance/interfaces/api/transactions.py:l12) importando `app.models.finance.account.Account`.
5. Testes (`tests/fin/test_crud_fin.py`) ainda dependem dos modelos em `app.models.finance.*`, quebrando o isolamento hexagonal.
6. `app/models/finance/__init__.py` recria exports apontando para a camada de infraestrutura, mantendo acoplamento indevido com o núcleo legado.
7. Ausência de contratos de repositório na camada `domain/repositories` conforme arquitetura prevista.
8. Em alguns casos, use cases executam queries SQL diretamente ao invés de delegar a repositórios/adapters (ex.: [`GenerateReportsUseCase.generate_balance_by_account`](app/modules/finance/application/use_cases/generate_reports.py:l51)).

## 2. Estratégia de Correção

1. **Unificar Modelos de Domínio**
   - Converter arquivos em `domain/entities` para **entidades de domínio puras** (dataclasses ou Pydantic) sem herança de `Base`.
   - Manter os modelos ORM apenas em `infrastructure/persistence/models`.
   - Remover `app/models/finance/__init__.py` recém-criado e toda dependência direta de modelos ORM fora da infraestrutura.

2. **Contratos de Repositório**
   - Criar interfaces em `domain/repositories` (ex.: `AccountRepository`, `TransactionRepository`, etc.) descrevendo operações necessárias pela camada de aplicação.
   - Implementar essas interfaces na camada de infraestrutura, provavelmente dentro de `infrastructure/persistence/repositories`.

3. **Use Cases Hexagonais**
   - Ajustar use cases para depender apenas das interfaces de repositório e serviços externos (ex.: serviço FX) injetados via construtor.
   - Mover lógica de agregação pesada (`GenerateReportsUseCase`) para repositórios específicos, retornando DTOs de domínio.

4. **Interfaces / APIs**
   - Adaptar endpoints para resolver dependências através de contêiner/componetização (Providers) que entreguem os repositórios/serviços necessários.
   - Garantir que `interfaces/api` trabalhe apenas com DTOs e schemas, nunca com ORM.

5. **Testes**
   - Atualizar testes unitários para usar fakes/mocks das interfaces de repositório ou fixtures ajustadas para os novos adapters ORM.
   - Confirmar que testes de integração end-to-end exercem apenas os adapters concretos da camada de infraestrutura.

6. **Remoção de Legado**
   - Apagar os arquivos em `app/models/finance/`.
   - Revisar scripts utilitários (`scripts/fin_diag.py`) para apontar para a camada de infraestrutura.
   - Validar que nenhum import `app.models.finance.*` permaneça no projeto (usar busca global).

7. **Eventos e Serviços Compartilhados**
   - Definir DTOs de eventos em `domain/events.py` alinhados ao documento de arquitetura.
   - Ajustar serviços de aplicação para publicar eventos via `core/events`.

## 3. Próximos Passos Imediatos

1. Redesenhar entidades de domínio (`domain/entities/`) como classes puras (sem SQLAlchemy).
2. Criar interfaces de repositório em `domain/repositories/`.
3. Implementar adapters de repositório em `infrastructure/persistence` usando os modelos SQLAlchemy existentes.
4. Refatorar `CreateTransferUseCase` e `GenerateReportsUseCase` para usar apenas as interfaces.
5. Atualizar endpoints e testes para consumir os novos contratos.

## 4. Métricas de Done

- `git grep "app.models.finance"` retorna vazio.
- Camadas seguem a arquitetura do documento (domínio sem ORM, aplicação sem acesso direto a infra).
- Testes automatizados (`pytest tests/fin`) passam.