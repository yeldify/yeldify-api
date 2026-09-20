# Yeldify API

**[hialth/yeldify-api](https://github.com/hialth/yeldify-api)** · Backend da plataforma de previsibilidade financeira **Yeldify**.

> O sistema que propõe (inteligência), mas o usuário decide (soberania absoluta).

[![CI](https://github.com/hialth/yeldify-api/actions/workflows/ci.yml/badge.svg)](https://github.com/hialth/yeldify-api/actions/workflows/ci.yml)

---

## Visão geral

API de finanças pessoais construída com **Python + FastAPI**, seguindo **arquitetura limpa em camadas**
(`domain` / `application` / `infrastructure`) e DDD — com *value objects* e agregados. O projeto é um
estudo de *seniorização* do autor (Product Manager) em engenharia de software com IA: prioriza código
limpo, boas práticas e testes, não escala de produção.

Frontend oficial em **[hialth/web](https://github.com/hialth/web)** (React + Vite).

## Funcionalidades

- **Orçamentos** — criação, edição, listagem paginada, arquivamento/reativação e **governança de teto**
  (justificativa obrigatória ao alterar orçamento com movimentações).
- **Lançamentos** — despesas e receitas, com `conta`, `método de pagamento` (cartão, espécie, PIX, outros)
  e flag `pendente` para transações órfãs da IA.
- **Dashboard micro** — resumo do mês: saldo, orçamentos com status, desvios e transações recentes.
- **Autenticação JWT** — `POST /auth/token` e `POST /auth/refresh` (usuários mock até haver base de dados real).
- **Persistência plugável** — repositório in-memory (default, dados efêmeros) ou **PostgreSQL** via `USE_POSTGRES=true`.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Presentation layer                              │
│   src/infrastructure/web — FastAPI app, APIRouters, schemas (Pydantic),  │
│   dependencies (DI dos use cases), auth JWT                              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  usa
┌───────────────────────────────▼─────────────────────────────────────────┐
│                           Application layer                              │
│   src/application/budgeting — use cases (Casos de Uso)                   │
│   criar/editar/listar orçamentos · lançar despesa/receita ·              │
│   editar/listar transações · dashboard micro                             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  depende apenas de IBudgetRepository
┌───────────────────────────────▼─────────────────────────────────────────┐
│                             Domain layer                                 │
│   src/domain/budgeting — regras puras, sem I/O                           │
│   Money (value object) · Budget (agregado) · Lancamento · exceptions     │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  implementa
┌───────────────────────────────▼─────────────────────────────────────────┐
│                     Infrastructure / Persistence                         │
│   src/infrastructure/persistence — IBudgetRepository                     │
│   InMemoryBudgetRepository (singleton) · PostgresSyncBudgetRepository    │
│   · repository_factory (switch por env) · seed de demonstração           │
└─────────────────────────────────────────────────────────────────────────┘
```

```mermaid
flowchart TD
    subgraph Web["Presentation (FastAPI)"]
        R[Routes /auth /orcamentos /despesas /receitas /transacoes /dashboard]
        S[Schemas Pydantic]
        D[Dependencies — DI dos Use Cases]
    end
    subgraph App["Application (Use Cases)"]
        UC1[Criar/Editar/Listar Orçamentos]
        UC2[Adicionar Despesa/Receita]
        UC3[Editar/Listar Transações]
        UC4[Dashboard Micro]
    end
    subgraph Dom["Domain (negócio puro)"]
        M[Money value object]
        B[Budget aggregate]
        L[Lancamento + TipoLancamento]
        E[Exceptions]
    end
    subgraph Infra["Persistence"]
        IF[IBudgetRepository]
        IM[InMemoryRepository]
        PG[PostgresRepository]
        SF[Seed Demo]
    end

    R --> D --> UC1 & UC2 & UC3 & UC4
    UC1 & UC2 & UC3 & UC4 --> B --> M & L
    UC1 & UC2 & UC3 & UC4 --> IF
    IF --> IM & PG
    SF --> IM
    E -.valida.-> B
```

## Stack

- **Python 3.11+** (CI usa 3.13)
- **FastAPI** + **Uvicorn** + **Pydantic v2**
- **SQLAlchemy** (persistência PostgreSQL, opcional)
- **python-jose** (JWT)
- **pytest** (testes unitários e de integração)

## Estrutura do repositório

```
api/
├── src/
│   ├── domain/budgeting/          # Entidades, value objects e regras de negócio
│   ├── application/budgeting/     # Use cases
│   └── infrastructure/
│       ├── persistence/           # Repositórios (in-memory / postgres) + seed
│       └── web/api/v1/            # FastAPI: app, routes, schemas, auth
├── tests/
│   ├── unit/                      # Testes de domínio e use cases
│   └── integration/               # Testes via TestClient (API)
├── scripts/                       # init_db.py, seed_demo.py
├── requirements/                  # base.txt (runtime), dev.txt (CI)
└── .github/workflows/ci.yml       # Pipeline GitHub Actions
```

## Como rodar

```bash
# 1) Ambiente
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt

# 2) API local (in-memory, com dados de demonstração)
SEED_DEMO=true uvicorn src.infrastructure.web.api.v1.api:app --reload
# Docs interativas: http://127.0.0.1:8000/docs

# 3) Testes
python -m pytest -q
```

### Usar PostgreSQL (opcional)

```env
USE_POSTGRES=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/yeldify
```

```bash
python scripts/init_db.py       # cria as tabelas
```

Para demo via Docker Postgres, ver [POSTGRES_SETUP.md](POSTGRES_SETUP.md).

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/token` | Gera token JWT (usuários mock: `user-123`, `user-456`) |
| `POST` | `/auth/refresh` | Renova token JWT |
| `POST` | `/orcamentos/` | Cria orçamento |
| `GET` | `/orcamentos/` | Lista paginada (`page`, `page_size`, `sort_by`, `pasta`) |
| `PUT` | `/orcamentos/{id}` | Edita orçamento (parcial; exige `nota_governanca` em teto com movimentações) |
| `POST` | `/despesas/` | Adiciona despesa |
| `POST` | `/receitas/` | Adiciona receita |
| `GET` | `/transacoes/` | Lista lançamentos (`tipo`, `ano_mes`, paginado) |
| `GET` | `/dashboard/micro` | Resumo mensal (saldo, status dos orçamentos, desvios) |

Auth para testes: `user_id` via `?user_id=` ou header `Authorization: Bearer <token>`.

## Regras de negócio em destaque

- `validade_meses` restrito a `[1, 2, 3, 6, 9, 12]`; `end_date = hoje + 30 * validade`.
- Nome de orçamento **único por usuário**.
- Orçamento desativado não aceita lançamentos; dentro da validade, só desativa sem lançamentos.
- `saldo = limite + entradas − saídas` (pode ser negativo). Moeda fixa: **BRL**.
- **Governança (anti auto-sabotagem):** alterar teto de orçamento que já tem movimentações exige justificativa registrada em auditoria.

## CI/CD

`main` é protegida — mudanças entram via **Pull Request** (merge exclusivo do mantenedor).

| Job | O que valida | Barra? |
|-----|--------------|--------|
| **gate** | Roda apenas os testes alterados pela PR | ✅ |
| **suite** | Suíte completa (informativa — 7 falhas de baseline documentadas) | ❌ informativo |
| **smoke** | Sobe a API com `SEED_DEMO=true` e confere `/transacoes/` respondendo | ✅ |

## Documentação complementar

- `JWT_AUTH_SETUP.md` — fluxo de autenticação
- `POSTGRES_SETUP.md` — persistência PostgreSQL
- `docs/followup_*` — decisões e evolução do domínio
- Brand manual e arquitetura do produto: `documentacao/` do workspace raiz