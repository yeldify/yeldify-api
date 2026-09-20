from fastapi.testclient import TestClient
from src.infrastructure.web.api.v1.api import create_app
from src.infrastructure.web.api.v1.dependencies import get_budget_repository
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from datetime import date


def override_get_budget_repository_with_budget(budget_id: str, user_id: str, limite: float):
    def _provider():
        repo = InMemoryBudgetRepository()
        budget = Budget(
            id=budget_id,
            user_id=user_id,
            nome="Alimentação",
            categoria="Alimentação",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            limite=Money(limite, "BRL"),
        )
        repo._budgets[budget_id] = budget
        return repo
    return _provider


def test_adicionar_despesa_endpoint_success():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budget(
        budget_id="budget-1", user_id="user-fake", limite=1000.0
    )
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-1",
            "valor": 150.75,
            "data": "2026-08-27",
            "descricao": "Almoço no restaurante",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["budget_id"] == "budget-1"
    assert abs(data["valor"] - 150.75) < 0.001
    assert data["data"] == "2026-08-27"
    assert data["descricao"] == "Almoço no restaurante"
    # defaults for new fields
    assert data["categoria"] == "Outros"
    assert data["conta"] == "Não informada"
    assert data["metodo_pagamento"] == "outros"
    assert data["pendente"] is False


def test_adicionar_despesa_endpoint_com_conta_metodo_pendente():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budget(
        budget_id="budget-1", user_id="user-fake", limite=1000.0
    )
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-1",
            "valor": 42.0,
            "data": "2026-08-27",
            "descricao": "Uber",
            "categoria": "Transporte",
            "conta": "Cartão Nubank • Crédito",
            "metodo_pagamento": "cartao",
            "pendente": True,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["categoria"] == "Transporte"
    assert data["conta"] == "Cartão Nubank • Crédito"
    assert data["metodo_pagamento"] == "cartao"
    assert data["pendente"] is True


def test_adicionar_despesa_endpoint_metodo_invalido():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budget(
        budget_id="budget-1", user_id="user-fake", limite=1000.0
    )
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-1",
            "valor": 42.0,
            "data": "2026-08-27",
            "descricao": "Uber",
            "metodo_pagamento": "boleto",
        },
    )
    assert response.status_code == 422


def test_adicionar_despesa_endpoint_budget_not_found():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: InMemoryBudgetRepository()
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-999",
            "valor": 50.0,
            "data": "2026-08-27",
            "descricao": "Test",
        },
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_adicionar_despesa_endpoint_unauthorized():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budget(
        budget_id="budget-1", user_id="other-user", limite=500.0
    )
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-1",
            "valor": 100.0,
            "data": "2026-08-27",
            "descricao": "Test",
        },
    )
    assert response.status_code == 400
    assert "permission" in response.json()["detail"].lower()


def test_adicionar_despesa_endpoint_empty_description():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budget(
        budget_id="budget-1", user_id="user-fake", limite=500.0
    )
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-1",
            "valor": 30.0,
            "data": "2026-08-27",
            "descricao": "   ",
        },
    )
    assert response.status_code == 422


def test_adicionar_despesa_endpoint_negative_value():
    app = create_app()
    app.dependency_overrides[get_budget_repository] = override_get_budget_repository_with_budget(
        budget_id="budget-1", user_id="user-fake", limite=500.0
    )
    client = TestClient(app)

    response = client.post(
        "/despesas/",
        json={
            "budget_id": "budget-1",
            "valor": -10.0,
            "data": "2026-08-27",
            "descricao": "Test",
        },
    )
    assert response.status_code == 400
    assert "Valor da despesa deve ser maior que zero" in response.json()["detail"]
