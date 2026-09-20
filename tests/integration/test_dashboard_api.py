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
        limite=Money(800.0, "BRL"),
    )
    b_alim.adicionar_lancamento(Lancamento(
        id="l1", budget_id=b_alim.id, valor=Money(850.0, "BRL"),
        data=date(2026, 9, 15), descricao="Ifood", tipo=TipoLancamento.SAIDA,
        categoria="Restaurante",
    ))
    b_alim.adicionar_lancamento(Lancamento(
        id="l2", budget_id=b_alim.id, valor=Money(3000.0, "BRL"),
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
        limite=Money(400.0, "BRL"),
    )
    b_transp.adicionar_lancamento(Lancamento(
        id="l3", budget_id=b_transp.id, valor=Money(340.0, "BRL"),
        data=date(2026, 9, 10), descricao="Uber", tipo=TipoLancamento.SAIDA,
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


def test_dashboard_micro_estrutura():
    client = make_app()
    response = client.get("/dashboard/micro", params={"user_id": "user-123", "ano_mes": "2026-09"})
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"resumo", "orcamentos", "desvios", "transacoes_recentes"}
    assert data["resumo"]["total_despesas"] == 1190.0  # 850 + 340
    assert data["resumo"]["total_receitas"] == 3000.0
    assert data["resumo"]["saldo_disponivel"] == 1810.0
    assert data["resumo"]["qtd_orcamentos_ativos"] == 2


def test_dashboard_micro_orcamentos_com_status():
    client = make_app()
    data = client.get("/dashboard/micro", params={"user_id": "user-123", "ano_mes": "2026-09"}).json()
    by_id = {o["id"]: o for o in data["orcamentos"]}
    assert by_id["b1"]["gasto"] == 850.0
    assert by_id["b1"]["teto"] == 800.0
    assert by_id["b1"]["percentual"] == 106.2  # 850/800*100 = 106.25 -> 106.2 (banker's)
    assert by_id["b1"]["status"] == "estourado"
    assert by_id["b2"]["status"] == "atencao"  # 85%


def test_dashboard_micro_desvios():
    client = make_app()
    data = client.get("/dashboard/micro", params={"user_id": "user-123", "ano_mes": "2026-09"}).json()
    assert [d["budget_id"] for d in data["desvios"]] == ["b1", "b2"]
    assert data["desvios"][0]["excedente"] == 50.0


def test_dashboard_micro_transacoes_recentes():
    client = make_app()
    data = client.get("/dashboard/micro", params={"user_id": "user-123", "ano_mes": "2026-09"}).json()
    assert len(data["transacoes_recentes"]) == 3
    datas = [t["data"] for t in data["transacoes_recentes"]]
    assert datas == sorted(datas, reverse=True)


def test_dashboard_micro_sem_dados():
    repo = InMemoryBudgetRepository()
    app = create_app()
    app.dependency_overrides[get_budget_repository] = lambda: repo
    client = TestClient(app)
    response = client.get("/dashboard/micro", params={"user_id": "user-999"})
    assert response.status_code == 200
    data = response.json()
    assert data["resumo"]["total_despesas"] == 0.0
    assert data["orcamentos"] == []
    assert data["desvios"] == []