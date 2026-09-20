# CLAUDE.md

## Visão geral
API de finanças pessoais ("Yeldify API", v0.1.0) construída com **Python 3.11 + FastAPI**,
focada no módulo de **orçamentos**. Segue arquitetura limpa em camadas
(`domain` / `application` / `infrastructure`).

## Objetivo do projeto
Projeto de aprendizagem: **seniorizar o autor (Product Manager) em desenvolvimento de software
com IA**. O foco está em código limpo, boas práticas (arquitetura em camadas, testes,
DDD value objects / agregados) e uso de ferramentas de IA como apoio ao desenvolvimento —
não em escala de produção.

## Arquitetura

### Domain — `src/domain/budgeting/`
Entidades e regras puras, sem dependência externa.
- `money.py` — `Money`: value object (frozen) com operações aritméticas e checagem de moeda.
- `budget.py` — `Budget`: agregado do orçamento (ativo/inativo, saldo, lançamentos, regras de desativação).
- `lancamento.py` — `Lancamento` (ENTRADA/SAIDA) e `TipoLancamento`.
- `expense.py` — `Expense`: modelo antigo, atualmente não utilizado.
- `exceptions.py` — `BudgetInactiveException`, `BudgetHasTransactionsException`.

### Application — `src/application/budgeting/`
Use cases, dependem apenas de `IBudgetRepository`:
- `criar_orcamento.py` — `CriarOrcamentoUseCase`
- `editar_orcamento.py` — `EditarOrcamentoUseCase`
- `list_orcamentos.py` — `ListarOrcamentosUseCase` (ordenação + paginação)
- `add_expense.py` — `AdicionarDespesaUseCase`
- `criar_orcamento.py` — `CriarOrcamentoUseCase` **(não possui endpoint ainda)**

### Infrastructure — `src/infrastructure/`
- `persistence/repositories.py` — interface `IBudgetRepository`
- `persistence/in_memory_budget_repository.py` — `InMemoryBudgetRepository` (sem banco; estado se perde ao reiniciar)
- `web/api/v1/api.py` — `create_app()` monta a aplicação FastAPI
- `web/api/v1/dependencies.py` — injeção de dependência dos use cases
- `web/api/v1/routes/` — `orcamentos.py`, `despesas.py`
- `web/api/v1/schemas/` — `orcamento_schema.py`, `orcamento_update_schema.py`, `despesa_schema.py`

## Regras de negócio
- `validade_meses` deve ser um de `[1, 2, 3, 6, 9, 12]`.
- `end_date` é calculado como `today + 30 * validade_meses` (aproximação de mês).
- Nome de orçamento deve ser **único por usuário**.
- Orçamento desativado **não aceita** novos lançamentos.
- Dentro da validade, só pode ser desativado **sem lançamentos**; expirado pode ser desativado com lançamentos.
- `saldo = limite + entradas − saídas` (pode ser negativo).
- Validade de orçamento **expirado** não pode ser editada.
- Moeda fixa atual: **BRL**.

## Endpoints
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/token` | Gera token JWT (mock de usuários) |
| POST | `/auth/refresh` | Renova token JWT |
| POST | `/orcamentos/` | Cria um orçamento |
| GET | `/orcamentos/` | Lista orçamentos ativos paginado: `{items, total, page, page_size}` |
| PUT | `/orcamentos/{budget_id}` | Edita um orçamento (PUT parcial: nome, valor, validade_meses, ativo) |
| POST | `/despesas/` | Adiciona despesa a um orçamento |
| POST | `/receitas/` | Adiciona receita a um orçamento |
| GET | `/transacoes/` | Lista lançamentos de todos os orçamentos (filtros `tipo`, `ano_mes`; paginado) |
| GET | `/dashboard/micro` | Resumo do mês do painel micro (saldo, orçamentos com status, desvios, transações recentes) |

`OrcamentoResponse` expõe `gasto` (só SAÍDAS), além de `valor_restante`, `valor_planejado` e `ativo`. `GET /transacoes/` entrega o subset do domínio atual (`Lancamento` tem `conta`/`pendente`/`metodo_pagamento` — ver `docs/followup_lancamento_conta_pendente.md`).

## Comandos
```bash
# Instalar dependências
pip install -r requirements/base.txt

# Instalar pytest (ambiente de desenvolvimento)
pip install pytest

# Rodar a API localmente
uvicorn src.infrastructure.web.api.v1.api:app --reload

# Rodar todos os testes
python -m pytest -q

# Rodar apenas unit ou integração
python -m pytest tests/unit -q
python -m pytest tests/integration -q
```

## Convenções
- Respeitar as camadas: domínio sem I/O, use cases só via `IBudgetRepository`, web apenas na camada de infra.
- Erros de domínio/validação devem levantar `ValueError`; rotas convertem `ValueError` → **HTTP 400** e erros inesperados → **HTTP 500**.
- Novos schemas/rotas devem manter o padrão pydantic + `APIRouter` + dependências.
- A autenticação é placeholder: `user_id` via query param ou `user-fake`.
- Não commitar `__pycache__/*.pyc` (ainda não há `.gitignore`).

## Pendências conhecidas
- Repositório in-memory é singleton (persiste entre requests), mas os dados se perdem ao reiniciar o processo.
- Auth ainda é placeholder: `user_id` via query param ou token JWT de mock (`/auth/token` com `user-123`/`user-456`).
- Seed demo: roda no startup da API somente com env `SEED_DEMO=true` (`_maybe_seed_demo_data()` em `api.py`); `scripts/seed_demo.py` usa o módulo `src/infrastructure/persistence/seed.py`.
- Testes: alguns divergem do comportamento atual e estão quebrados no baseline (negativos em `Money`, use case de despesas com `FakeBudgetRepository` sem `list_by_user_id`, `Budget(budget_id=...)` em testes de API, datas hardcoded de `test_budget`).

## CORS / Front
- CORS liberado para `localhost:5173`.
- O front (`web/`) consome esta API via proxy do Vite: `/api` → `http://localhost:8000` (rewrite remove o prefixo `/api`). O Vite proxy roda o front redirecionando requests; alternativamente, `VITE_API_URL` aponta direto para o back.
- `web/src/hooks/useMockData.ts` tenta a API primeiro e cai para os mocks locais de `web/src/mocks/` se a API estiver indisponível (flag `usandoApi`).