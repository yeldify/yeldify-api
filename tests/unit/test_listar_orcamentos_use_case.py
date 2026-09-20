import pytest
from datetime import date, timedelta
from decimal import Decimal
from src.application.budgeting.list_orcamentos import ListarOrcamentosUseCase
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento


def make_budget(budget_id: str, nome: str, categoria: str, valor: float, days_ago: int = 0, ativo: bool = True) -> Budget:
    """Helper to create a budget with given criado há days_ago days."""
    criado = date.today() - timedelta(days=days_ago)
    budget = Budget(
        id=budget_id,
        user_id="user-123",
        nome=nome,
        categoria=categoria,
        start_date=criado,
        end_date=criado + timedelta(days=30),  # 1 month validity for simplicity
        limite=Money(valor, "BRL"),
        _ativo=ativo,
        created_at=criado,
    )
    return budget


def test_listar_orcamentos_empty():
    repo = InMemoryBudgetRepository()
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123")
    assert result.items == []
    assert result.total == 0


def test_listar_orcamentos_single():
    repo = InMemoryBudgetRepository()
    budget = make_budget("b1", "Alimentação", "Essencial", 1000.0)
    repo.save(budget)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123")
    assert len(result.items) == 1
    assert result.total == 1
    assert result.items[0].id == "b1"
    assert result.items[0].nome == "Alimentação"


def test_listar_orcamentos_multiple_default_sort_by_nome():
    repo = InMemoryBudgetRepository()
    # Create budgets with names that will sort: "Delta", "Alpha", "Charlie"
    b1 = make_budget("b1", "Delta", "Essencial", 500.0, days_ago=10)
    b2 = make_budget("b2", "Alpha", "Essencial", 300.0, days_ago=5)
    b3 = make_budget("b3", "Charlie", "Essencial", 700.0, days_ago=1)
    for b in (b1, b2, b3):
        repo.save(b)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123")
    assert [b.nome for b in result.items] == ["Alpha", "Charlie", "Delta"]
    assert result.total == 3


def test_listar_orcamentos_sort_by_valor_restante():
    repo = InMemoryBudgetRepository()
    b1 = make_budget("b1", "A", "Essencial", 1000.0)
    b2 = make_budget("b2", "B", "Essencial", 1000.0)
    b3 = make_budget("b3", "C", "Essencial", 1000.0)
    lanc_entry = Lancamento(
        id="l1",
        budget_id=b2.id,
        valor=Money(200.0, "BRL"),
        data=date.today(),
        descricao="Entrada",
        tipo=TipoLancamento.ENTRADA,
    )
    lanc_exit = Lancamento(
        id="l2",
        budget_id=b3.id,
        valor=Money(300.0, "BRL"),
        data=date.today(),
        descricao="Saida",
        tipo=TipoLancamento.SAIDA,
    )
    b2.adicionar_lancamento(lanc_entry)
    b3.adicionar_lancamento(lanc_exit)
    for b in (b1, b2, b3):
        repo.save(b)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123", sort_by="valor_restante")
    # Expected order by saldo ascending: b3 (700), b1 (1000), b2 (1200)
    assert [b.saldo.amount for b in result.items] == [Decimal('700'), Decimal('1000'), Decimal('1200')]
    assert [b.nome for b in result.items] == ["C", "A", "B"]


def test_listar_orcamentos_sort_by_valor_planejado():
    repo = InMemoryBudgetRepository()
    b1 = make_budget("b1", "Low", "Essencial", 500.0)
    b2 = make_budget("b2", "Medium", "Essencial", 1000.0)
    b3 = make_budget("b3", "High", "Essencial", 1500.0)
    for b in (b1, b2, b3):
        repo.save(b)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123", sort_by="valor_planejado")
    assert [b.limite.amount for b in result.items] == [Decimal('500'), Decimal('1000'), Decimal('1500')]
    assert [b.nome for b in result.items] == ["Low", "Medium", "High"]


def test_listar_orcamentos_sort_by_data_criacao():
    repo = InMemoryBudgetRepository()
    oldest = make_budget("b1", "Oldest", "Essencial", 100.0, days_ago=20)
    middle = make_budget("b2", "Middle", "Essencial", 200.0, days_ago=10)
    newest = make_budget("b3", "Newest", "Essencial", 300.0, days_ago=0)
    for b in (oldest, middle, newest):
        repo.save(b)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123", sort_by="data_criacao")
    assert [b.nome for b in result.items] == ["Oldest", "Middle", "Newest"]
    assert result.items[0].created_at <= result.items[1].created_at <= result.items[2].created_at


def test_listar_orcamentos_pagination():
    repo = InMemoryBudgetRepository()
    for i in range(15):
        nome = f"Budget {i:02d}"
        budget = make_budget(f"bid{i}", nome, "Essencial", 100.0 + i)
        repo.save(budget)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    page1 = use_case.execute(user_id="user-123", page=1, page_size=10)
    assert len(page1.items) == 10
    assert page1.total == 15
    assert [b.nome for b in page1.items] == [f"Budget {i:02d}" for i in range(10)]
    page2 = use_case.execute(user_id="user-123", page=2, page_size=10)
    assert len(page2.items) == 5
    assert page2.total == 15
    assert [b.nome for b in page2.items] == [f"Budget {i:02d}" for i in range(10, 15)]
    page3 = use_case.execute(user_id="user-123", page=3, page_size=10)
    assert page3.items == []
    assert page3.total == 15


def test_listar_orcamentos_inactive_not_included():
    repo = InMemoryBudgetRepository()
    active_budget = make_budget("active", "Active", "Essencial", 500.0, ativo=True)
    inactive_budget = make_budget("inactive", "Inactive", "Essencial", 500.0, ativo=False)
    repo.save(active_budget)
    repo.save(inactive_budget)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123")
    assert len(result.items) == 1
    assert result.total == 1
    assert result.items[0].id == "active"


def test_listar_orcamentos_invalid_page_page_size():
    repo = InMemoryBudgetRepository()
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="page must be >= 1"):
        use_case.execute(user_id="user-123", page=0)
    with pytest.raises(ValueError, match="page_size must be >= 1"):
        use_case.execute(user_id="user-123", page_size=0)


def test_listar_orcamentos_user_id_validation():
    repo = InMemoryBudgetRepository()
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="user_id must be a non-empty string"):
        use_case.execute(user_id="")


def test_listar_orcamentos_sort_by_invalid_field_fallback_to_nome():
    repo = InMemoryBudgetRepository()
    b1 = make_budget("b1", "Zebra", "Essencial", 100.0)
    b2 = make_budget("b2", "Apple", "Essencial", 200.0)
    repo.save(b1)
    repo.save(b2)
    use_case = ListarOrcamentosUseCase(budget_repository=repo)
    result = use_case.execute(user_id="user-123", sort_by="invalid_field")
    assert [b.nome for b in result.items] == ["Apple", "Zebra"]