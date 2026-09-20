# Follow-up: conta, pendente e método de pagamento no Lançamento

Status: ✅ implementado (back + front)

## Contexto

O domínio `Lancamento` (`src/domain/budgeting/lancamento.py`) modelava apenas:

- `id`, `budget_id`, `valor: Money`, `data`, `descricao`, `tipo` (`ENTRADA`/`SAIDA`), `categoria`, `data_criacao`.

Porém as telas do front (`web/`) usam campos que **não existiam** nesse modelo:

- **`conta`** — ex.: "Cartão Nubank • Crédito", "Carteira Física • Espécie" (`dashboard/micro.tsx`, mocks de `transacoes.json`).
- **Método de pagamento** — `cartao` vs `especie` (dinheiro vivo). Atenção: no back, `tipo` significa ENTRADA/SAIDA; o método de pagamento virou campo próprio (`metodo_pagamento`).
- **`pendente`** — transações sem categoria conhecida, isoladas com tag amarela.

Como consequência, `GET /transacoes` e `GET /dashboard/micro` entregavam apenas o subset do domínio atual (sem `conta`, sem `pendente`, sem cartão/espécie).

## Implementação

### 1. Domain ✅ (`src/domain/budgeting/lancamento.py`)
- Novo enum `MetodoPagamento` (`CARTAO="cartao"`, `ESPECIE="especie"`, `PIX="pix"`, `OUTROS="outros"`), valores compatíveis com o front.
- `Lancamento` ganhou campos opcionais com default:
  ```python
  conta: str = "Não informada"
  metodo_pagamento: MetodoPagamento = MetodoPagamento.OUTROS
  pendente: bool = False
  ```
- Validação em `__post_init__` para os três campos.

### 2. Application ✅
- `AdicionarDespesaUseCase` (`add_expense.py`) e `AdicionarReceitaUseCase` (`add_receita.py`) aceitam e encaminham `conta`, `metodo_pagamento`, `pendente`.
- Schemas `DespesaCreate`/`ReceitaCreate` expõem os campos (opcionais).

### 3. Persistência ✅
- `LancamentoModel` (`models.py`) ganhou as colunas `conta`, `metodo_pagamento`, `pendente`.
- `PostgresSyncBudgetRepository` mapeia ida/volta em `_budget_to_model` / `_model_to_budget`.
- Repositório in-memory: sem mudança (o agregado guarda os campos).

### 4. API ✅
- `TransacaoResult` (via `ListarTransacoesUseCase`) expõe `conta`, `metodo_pagamento`, `pendente`; `GET /transacoes/` devolve os campos.
- `DespesaResponse`/`ReceitaResponse` e `GET /dashboard/micro` repassam `conta`, `metodo_pagamento`, `pendente`.

### 5. Front ✅ (`web/`)
- Componente reutilizável `src/components/TransacaoItem.tsx` — mostra data, descrição, tag de categoria, `conta`, sinal e valor; renderiza tag tracejada amarela `[Pendente]` quando `pendente` ou sem categoria.
- `useMockData.ts` — tipo `Transacao` alinhado ao back: `tipo: 'ENTRADA' | 'SAIDA'`, `metodo_pagamento: 'cartao' | 'especie' | 'pix' | 'outros'`, `conta`, `pendente`.
- `transacoes.json` — mock atualizado com os mesmos campos (não usa mais `tipo` como método de pagamento).
- `dashboard/micro.tsx` — transações e orçamentos passam a vir do hook `useMockData` (dados reais dos mocks), renderizados via `TransacaoItem`; remove `conta` hardcoded.
- `pages/transacoes/index.tsx` — timeline consome o mock, exibe `conta` e tag `[Pendente]`; drawer de novo lançamento já previa Conta e Cartão/Dinheiro Vivo.

## Decisões tomadas
- `metodo_pagamento` foi implementado como **enum no domínio** (`MetodoPagamento`), alinhado ao padrão `TipoLancamento`, com valores em string compatíveis com o front (`cartao`/`especie`/`pix`/`outros`).
- Transação verdadeiramente "órfã" (sem `budget_id`) **permanece fora do escopo**: o modelo ainda exige vínculo com orçamento.
- `categoria` vazia/sem classificação é o critério usado no front para marcar a tag `[Pendente]` (junto com o campo `pendente`).

## Impacto técnico
- Backward compatible: os novos campos são opcionais com default — testes existentes de `Lancamento` continuam válidos.
- Cobertura: tests de unidade de `AdicionarDespesaUseCase` e de integração de `POST /despesas/` com `conta`/`metodo_pagamento`/`pendente`.