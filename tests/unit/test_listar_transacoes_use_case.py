import pytest
from datetime import date, timedelta
from src.application.budgeting.listar_transacoes import ListarTransacoesUseCase, parse_ano_mes
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento


def make_budget(budget_id: str, nome: str, categoria: str, limite: float, user_id="user-123") -> Budget:
    return Budget(
        id=budget_id,
        user_id=user_id,
        nome=nome,
        categoria=categoria,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(limite, "BRL"),
        _ativo=True,
    )


def add_lanc(budget: Budget, lanc_id: str, valor: float, data: date, descricao: str, tipo: TipoLancamento, categoria: str = "Outros"):
    budget.adicionar_lancamento(Lancamento(
        id=lanc_id,
        budget_id=budget.id,
        valor=Money(valor, "BRL"),
        data=data,
        descricao=descricao,
        tipo=tipo,
        categoria=categoria,
    ))


def build_repo():
    repo = InMemoryBudgetRepository()
    b_alim = make_budget("b1", "Alimentação", "Essencial", 1500.0)
    add_lanc(b_alim, "l1", 85.90, date(2026, 9, 17), "Ifood", TipoLancamento.SAIDA, "Restaurante")
    add_lanc(b_alim, "l2", 1200.00, date(2026, 9, 5), "Salário", TipoLancamento.ENTRADA, "Renda")
    add_lanc(b_alim, "l3", 40.00, date(2026, 8, 30), "Mercado agosto", TipoLancamento.SAIDA, "Supermercado")

    b_transp = make_budget("b2", "Transporte", "Essencial", 500.0)
    add_lanc(b_transp, "l4", 28.50, date(2026, 9, 16), "Uber", TipoLancamento.SAIDA, "Transporte")

    repo.save(b_alim)
    repo.save(b_transp)
    return repo


def test_parse_ano_mes():
    inicio, fim = parse_ano_mes("2026-09")
    assert inicio == date(2026, 9, 1)
    assert fim == date(2026, 10, 1)


def test_parse_ano_mes_dezembro():
    inicio, fim = parse_ano_mes("2026-12")
    assert inicio == date(2026, 12, 1)
    assert fim == date(2027, 1, 1)


def test_parse_ano_mes_invalido():
    with pytest.raises(ValueError, match="ano_mes"):
        parse_ano_mes("2026/09")


def test_listar_transacoes_agrega_todos_orcamentos():
    repo = build_repo()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    items, total = use_case.execute(user_id="user-123")
    assert total == 4
    # ordenação por data desc: l1 (17/09), l4 (16/09), l2 (05/09), l3 (30/08)
    assert [t.id for t in items] == ["l1", "l4", "l2", "l3"]


def test_listar_transacoes_filtro_ano_mes():
    repo = build_repo()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    items, total = use_case.execute(user_id="user-123", ano_mes="2026-09")
    assert total == 3
    assert {t.id for t in items} == {"l1", "l2", "l4"}


def test_listar_transacoes_filtro_tipo():
    repo = build_repo()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    items, total = use_case.execute(user_id="user-123", tipo="ENTRADA")
    assert total == 1
    assert items[0].id == "l2"


def test_listar_transacoes_paginacao():
    repo = build_repo()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    items, total = use_case.execute(user_id="user-123", page=1, page_size=2)
    assert total == 4
    assert len(items) == 2
    assert [t.id for t in items] == ["l1", "l4"]
    items2, _ = use_case.execute(user_id="user-123", page=2, page_size=2)
    assert [t.id for t in items2] == ["l2", "l3"]


def test_listar_transacoes_enriquecidas_com_orcamento():
    repo = build_repo()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    items, _ = use_case.execute(user_id="user-123")
    l1 = next(t for t in items if t.id == "l1")
    assert l1.budget_id == "b1"
    assert l1.budget_nome == "Alimentação"
    assert l1.budget_categoria == "Essencial"
    assert l1.valor == 85.90
    assert l1.categoria == "Restaurante"
    assert l1.tipo == "SAIDA"


def test_listar_transacoes_sem_resultado():
    repo = InMemoryBudgetRepository()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    items, total = use_case.execute(user_id="user-123")
    assert items == []
    assert total == 0


def test_listar_transacoes_validacoes():
    repo = InMemoryBudgetRepository()
    use_case = ListarTransacoesUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="user_id"):
        use_case.execute(user_id="")
    with pytest.raises(ValueError, match="tipo"):
        use_case.execute(user_id="user-123", tipo="INVALIDO")
    with pytest.raises(ValueError, match="page"):
        use_case.execute(user_id="user-123", page=0)
    with pytest.raises(ValueError, match="page_size"):
        use_case.execute(user_id="user-123", page_size=0)