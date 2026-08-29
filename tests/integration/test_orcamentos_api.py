from fastapi.testclient import TestClient
from src.infrastructure.web.api.v1.api import create_app
from src.infrastructure.web.api.v1.dependencies import get_budget_repository
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from datetime import date, timedelta
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento

def override_get_budget_repository_with_budgets(budgets):
    """Override dependency to return a repository with the given budgets."""
    def _provider():
        repo = InMemoryBudgetRepository()
        for b in budgets:
            repo._budgets[b.id] = b
        return repo
    return _provider

def test_listar_orcamentos_empty():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: InMemoryBudgetRepository()
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123"})
    assert response.status_code == 200
    assert response.json() == []

def test_listar_orcamentos_single():
    # Create a budget
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Alimentação",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([budget])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "b1"
    assert data[0]["nome"] == "Alimentação"
    assert data[0]["valor_restante"] == 1000.0  # saldo = limite (no transactions)
    assert data[0]["valor_planejado"] == 1000.0
    assert data[0]["data_criacao"] == hoje.isoformat()

def test_listar_orcamentos_multiple_sort_by_nome():
    hoje = date.today()
    b1 = Budget(
        id="b1",
        user_id="user-123",
        nome="Delta",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b2 = Budget(
        id="b2",
        user_id="user-123",
        nome="Alpha",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(300.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b3 = Budget(
        id="b3",
        user_id="user-123",
        nome="Charlie",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(700.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([b1, b2, b3])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "sort_by": "nome"})
    assert response.status_code == 200
    data = response.json()
    assert [item["nome"] for item in data] == ["Alpha", "Charlie", "Delta"]

def test_listar_orcamentos_pagination():
    hoje = date.today()
    budgets = []
    for i in range(15):
        budgets.append(Budget(
            id=f"bid{i}",
            user_id="user-123",
            nome=f"Budget {i:02d}",
            categoria="Essencial",
            start_date=hoje,
            end_date=hoje + timedelta(days=30),
            limite=Money(100.0 + i, "BRL"),
            _ativo=True,
            created_at=hoje,
        ))
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets(budgets)
    client = TestClient(app)
    # Page 1, size 10
    response = client.get("/orcamentos/", params={"user_id": "user-123", "page": 1, "page_size": 10})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert [item["nome"] for item in data] == [f"Budget {i:02d}" for i in range(10)]
    # Page 2, size 10
    response = client.get("/orcamentos/", params={"user_id": "user-123", "page": 2, "page_size": 10})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert [item["nome"] for item in data] == [f"Budget {i:02d}" for i in range(10, 15)]
    # Page 3, size 10 -> empty
    response = client.get("/orcamentos/", params={"user_id": "user-123", "page": 3, "page_size": 10})
    assert response.status_code == 200
    assert response.json() == []

def test_listar_orcamentos_inactive_not_included():
    hoje = date.today()
    active = Budget(
        id="active",
        user_id="user-123",
        nome="Active",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    inactive = Budget(
        id="inactive",
        user_id="user-123",
        nome="Inactive",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=False,
        created_at=hoje,
    )
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([active, inactive])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "active"

def test_listar_orcamentos_sort_by_valor_restante():
    hoje = date.today()
    # Budgets with same limit but different transactions to affect saldo
    b1 = Budget(
        id="b1",
        user_id="user-123",
        nome="A",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b2 = Budget(
        id="b2",
        user_id="user-123",
        nome="B",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b3 = Budget(
        id="b3",
        user_id="user-123",
        nome="C",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    # Add lancamentos
    # b1: no transactions -> saldo = 1000
    # b2: entrada 200 -> saldo = 1200
    # b3: saida 300 -> saldo = 700
    lanc_entry = Lancamento(
        id="l1",
        budget_id=b2.id,
        valor=Money(200.0, "BRL"),
        data=hoje,
        descricao="Entrada",
        tipo=TipoLancamento.ENTRADA,
    )
    lanc_exit = Lancamento(
        id="l2",
        budget_id=b3.id,
        valor=Money(300.0, "BRL"),
        data=hoje,
        descricao="Saida",
        tipo=TipoLancamento.SAIDA,
    )
    b2.adicionar_lancamento(lanc_entry)
    b3.adicionar_lancamento(lanc_exit)
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([b1, b2, b3])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "sort_by": "valor_restante"})
    assert response.status_code == 200
    data = response.json()
    # Expected ascending: 700, 1000, 1200
    assert [item["valor_restante"] for item in data] == [700.0, 1000.0, 1200.0]
    assert [item["nome"] for item in data] == ["C", "A", "B"]

def test_listar_orcamentos_sort_by_valor_planejado():
    hoje = date.today()
    b1 = Budget(
        id="b1",
        user_id="user-123",
        nome="Low",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b2 = Budget(
        id="b2",
        user_id="user-123",
        nome="Medium",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b3 = Budget(
        id="b3",
        user_id="user-123",
        nome="High",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([b1, b2, b3])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "sort_by": "valor_planejado"})
    assert response.status_code == 200
    data = response.json()
    assert [item["valor_planejado"] for item in data] == [500.0, 1000.0, 1500.0]
    assert [item["nome"] for item in data] == ["Low", "Medium", "High"]

def test_listar_orcamentos_sort_by_data_criacao():
    hoje = date.today()
    oldest = Budget(
        id="b1",
        user_id="user-123",
        nome="Oldest",
        categoria="Essencial",
        start_date=hoje - timedelta(days=20),
        end_date=hoje - timedelta(days=20) + timedelta(days=30),
        limite=Money(100.0, "BRL"),
        _ativo=True,
        created_at=hoje - timedelta(days=20),
    )
    middle = Budget(
        id="b2",
        user_id="user-123",
        nome="Middle",
        categoria="Essencial",
        start_date=hoje - timedelta(days=10),
        end_date=hoje - timedelta(days=10) + timedelta(days=30),
        limite=Money(200.0, "BRL"),
        _ativo=True,
        created_at=hoje - timedelta(days=10),
    )
    newest = Budget(
        id="b3",
        user_id="user-123",
        nome="Newest",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(300.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([oldest, middle, newest])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "sort_by": "data_criacao"})
    assert response.status_code == 200
    data = response.json()
    assert [item["nome"] for item in data] == ["Oldest", "Middle", "Newest"]
    # Check dates are in ascending order (oldest first)
    dates = [item["data_criacao"] for item in data]
    assert dates == sorted(dates)

def test_listar_orcamentos_invalid_page():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: InMemoryBudgetRepository()
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "page": 0})
    assert response.status_code == 400
    assert "page must be >= 1" in response.json()["detail"]

def test_listar_orcamentos_invalid_page_size():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: InMemoryBudgetRepository()
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "page_size": 0})
    assert response.status_code == 400
    assert "page_size must be >= 1" in response.json()["detail"]

def test_listar_orcamentos_user_id_validation():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: InMemoryBudgetRepository()
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": ""})
    assert response.status_code == 400
    assert "user_id must be a non-empty string" in response.json()["detail"]

def test_listar_orcamentos_sort_by_invalid_fallback_to_nome():
    hoje = date.today()
    b1 = Budget(
        id="b1",
        user_id="user-123",
        nome="Zebra",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(100.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b2 = Budget(
        id="b2",
        user_id="user-123",
        nome="Apple",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(200.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budgets([b1, b2])
    client = TestClient(app)
    response = client.get("/orcamentos/", params={"user_id": "user-123", "sort_by": "invalid_field"})
    assert response.status_code == 200
    data = response.json()
    # Should fallback to nome (alphabetical)
    assert [item["nome"] for item in data] == ["Apple", "Zebra"]