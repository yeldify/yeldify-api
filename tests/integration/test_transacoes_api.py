from fastapi.testclient import TestClient
from datetime import date

from src.infrastructure.web.api.v1.api import create_app
from src.infrastructure.web.api.v1.dependencies import get_budget_repository
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento


def build_repo():
    repo = InMemoryBudgetRepository()
    b_alim = Budget(
        id="b1",
        user_id="user-123",
        nome="Alimentação",
        categoria="Essencial",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(1500.0, "BRL"),
    )
    b_alim.adicionar_lancamento(Lancamento(
        id="l1", budget_id=b_alim.id, valor=Money(85.90, "BRL"),
        data=date(2026, 9, 17), descricao="Ifood", tipo=TipoLancamento.SAIDA,
        categoria="Restaurante",
    ))
    b_alim.adicionar_lancamento(Lancamento(
        id="l2", budget_id=b_alim.id, valor=Money(1200.0, "BRL"),
        data=date(2026, 9, 5), descricao="Salário", tipo=TipoLancamento.ENTRADA,
        categoria="Renda",
    ))
    b_transp = Budget(
        id="b2",
        user_id="user-123",
        nome="Transporte",
        categoria="Essencial",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(500.0, "BRL"),
    )
    b_transp.adicionar_lancamento(Lancamento(
        id="l3", budget_id=b_transp.id, valor=Money(28.50, "BRL"),
        data=date(2026, 9, 16), descricao="Uber", tipo=TipoLancamento.SAIDA,
        categoria="Transporte",
    ))
    repo.save(b_alim)
    repo.save(b_transp)
    return repo


def make_app():
    repo = build_repo()
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: repo
    return TestClient(app)


def test_listar_transacoes_envelope_e_campos():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and "total" in data and "page" in data and "page_size" in data
    assert data["total"] == 3
    assert len(data["items"]) == 3
    first = data["items"][0]
    assert first["id"] == "l1"
    assert first["budget_id"] == "b1"
    assert first["budget_nome"] == "Alimentação"
    assert first["descricao"] == "Ifood"
    assert first["valor"] == 85.90
    assert first["data"] == "2026-09-17"
    assert first["categoria"] == "Restaurante"
    assert first["tipo"] == "SAIDA"


def test_listar_transacoes_filtro_ano_mes():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "ano_mes": "2026-09"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


def test_listar_transacoes_filtro_ano_mes_sem_resultados():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "ano_mes": "2025-01"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_listar_transacoes_filtro_tipo():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "tipo": "ENTRADA"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "l2"


def test_listar_transacoes_tipo_invalido_400():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "tipo": "INVALIDO"})
    assert response.status_code == 400


def test_listar_transacoes_ano_mes_invalido_400():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "ano_mes": "2026/09"})
    assert response.status_code == 400


def test_listar_transacoes_paginacao():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "page": 1, "page_size": 2})
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    response2 = client.get("/transacoes/", params={"user_id": "user-123", "page": 2, "page_size": 2})
    data2 = response2.json()
    assert len(data2["items"]) == 1


def test_listar_transacoes_filtro_budget_id():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "budget_id": "b2"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "l3"


def test_listar_transacoes_filtro_budget_id_sem_resultados():
    client = make_app()
    response = client.get("/transacoes/", params={"user_id": "user-123", "budget_id": "b-404"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_editar_transacao_categoria_success():
    client = make_app()
    response = client.patch(
        "/transacoes/l1",
        params={"user_id": "user-123"},
        json={"categoria": "Alimentação"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "l1"
    assert data["categoria"] == "Alimentação"
    assert data["descricao"] == "Ifood"
    # Confirm persistence via listagem
    list_response = client.get("/transacoes/", params={"user_id": "user-123"})
    item = next(t for t in list_response.json()["items"] if t["id"] == "l1")
    assert item["categoria"] == "Alimentação"


def test_editar_transacao_pendente_conta_metodo_success():
    client = make_app()
    response = client.patch(
        "/transacoes/l1",
        params={"user_id": "user-123"},
        json={"conta": "Carteira Física • Espécie", "metodo_pagamento": "especie", "pendente": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["conta"] == "Carteira Física • Espécie"
    assert data["metodo_pagamento"] == "especie"
    assert data["pendente"] is True


def test_editar_transacao_nao_encontrada_400():
    client = make_app()
    response = client.patch(
        "/transacoes/l-404",
        params={"user_id": "user-123"},
        json={"categoria": "X"},
    )
    assert response.status_code == 400


def test_editar_transacao_sem_campos_400():
    client = make_app()
    response = client.patch(
        "/transacoes/l1",
        params={"user_id": "user-123"},
        json={},
    )
    assert response.status_code == 400


def test_editar_transacao_categoria_invalida_422():
    client = make_app()
    response = client.patch(
        "/transacoes/l1",
        params={"user_id": "user-123"},
        json={"categoria": " "},
    )
    assert response.status_code == 422