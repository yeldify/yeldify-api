import pytest
from datetime import date
from src.application.budgeting.dashboard_micro import DashboardMicroUseCase
from src.application.budgeting.listar_transacoes import ListarTransacoesUseCase
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento


def make_budget(budget_id: str, nome: str, categoria: str, limite: float, ativo: bool = True) -> Budget:
    return Budget(
        id=budget_id,
        user_id="user-123",
        nome=nome,
        categoria=categoria,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(limite, "BRL"),
        _ativo=ativo,
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


def build_repo(setembro=True):
    repo = InMemoryBudgetRepository()

    b_alim = make_budget("b1", "Alimentação", "Essencial", 800.0)
    add_lanc(b_alim, "l1", 850.00, date(2026, 9, 15), "Ifood", TipoLancamento.SAIDA, "Restaurante")  # 106.25% -> estourado
    add_lanc(b_alim, "l2", 100.00, date(2026, 9, 3), "Mercado", TipoLancamento.SAIDA, "Supermercado")  # gasto total 950

    b_transp = make_budget("b2", "Transporte", "Essencial", 400.0)
    add_lanc(b_transp, "l3", 340.00, date(2026, 9, 10), "Uber", TipoLancamento.SAIDA, "Transporte")  # 85% -> atencao

    b_saude = make_budget("b3", "Saúde", "Essencial", 300.0)
    add_lanc(b_saude, "l4", 112.00, date(2026, 9, 8), "Farmácia", TipoLancamento.SAIDA, "Saúde")  # 37.3% -> ok

    b_arquivado = make_budget("b4", "Arquivado", "Investimentos", 500.0, ativo=False)

    if setembro:
        add_lanc(b_alim, "l6", 3000.00, date(2026, 9, 5), "Salário", TipoLancamento.ENTRADA, "Renda")

    for b in (b_alim, b_transp, b_saude, b_arquivado):
        repo.save(b)
    return repo


def make_use_case(setembro=True):
    repo = build_repo(setembro)
    return DashboardMicroUseCase(
        budget_repository=repo,
        listar_transacoes_use_case=ListarTransacoesUseCase(budget_repository=repo),
    ), repo


def test_dashboard_micro_resumo():
    use_case, _ = make_use_case(setembro=True)
    result = use_case.execute(user_id="user-123", ano_mes="2026-09")
    assert result.resumo.total_despesas == 950.0 + 340.0 + 112.0
    assert result.resumo.total_receitas == 3000.0
    assert result.resumo.saldo_disponivel == 3000.0 - (950.0 + 340.0 + 112.0)
    assert result.resumo.qtd_orcamentos_ativos == 3


def test_dashboard_micro_ignora_orcamentos_inativos():
    use_case, _ = make_use_case(setembro=True)
    result = use_case.execute(user_id="user-123", ano_mes="2026-09")
    # b4 é inativo -> não entra em orcamentos nem desvios nem totais
    nomes = [o.nome for o in result.orcamentos]
    assert nomes == ["Alimentação", "Transporte", "Saúde"]
    assert all(d.budget_id != "b4" for d in result.desvios)


def test_dashboard_micro_status_e_percentuais():
    use_case, _ = make_use_case(setembro=True)
    result = use_case.execute(user_id="user-123", ano_mes="2026-09")
    by_id = {o.id: o for o in result.orcamentos}
    assert by_id["b1"].gasto == 950.0
    assert by_id["b1"].percentual == 118.8  # 950/800*100
    assert by_id["b1"].status == "estourado"
    assert by_id["b2"].percentual == 85.0
    assert by_id["b2"].status == "atencao"
    assert by_id["b3"].status == "ok"


def test_dashboard_micro_desvios():
    use_case, _ = make_use_case(setembro=True)
    result = use_case.execute(user_id="user-123", ano_mes="2026-09")
    assert [d.budget_id for d in result.desvios] == ["b1", "b2"]  # ordenados por percentual desc
    estourado = next(d for d in result.desvios if d.budget_id == "b1")
    assert estourado.excedente == 150.0  # 950 - 800
    assert estourado.dias_restantes > 0


def test_dashboard_micro_transacoes_recentes():
    use_case, _ = make_use_case(setembro=True)
    result = use_case.execute(user_id="user-123", ano_mes="2026-09")
    assert len(result.transacoes_recentes) == 5
    # ordenadas por data desc
    datas = [t.data for t in result.transacoes_recentes]
    assert datas == sorted(datas, reverse=True)


def test_dashboard_micro_ano_mes_default():
    # Dados em mês distante (2030-05): o default (mês corrente) deve vir vazio
    repo = InMemoryBudgetRepository()
    b = make_budget("b1", "Alimentação", "Essencial", 800.0)
    add_lanc(b, "l1", 100.00, date(2030, 5, 15), "Mercado", TipoLancamento.SAIDA)
    repo.save(b)
    use_case = DashboardMicroUseCase(
        budget_repository=repo,
        listar_transacoes_use_case=ListarTransacoesUseCase(budget_repository=repo),
    )
    result = use_case.execute(user_id="user-123")
    assert result.resumo.total_despesas == 0.0
    assert result.resumo.total_receitas == 0.0
    assert result.transacoes_recentes == []


def test_dashboard_micro_sem_receitas():
    use_case, _ = make_use_case(setembro=False)
    result = use_case.execute(user_id="user-123", ano_mes="2026-09")
    assert result.resumo.total_receitas == 0.0
    assert result.resumo.saldo_disponivel == -(950.0 + 340.0 + 112.0)


def test_dashboard_micro_user_id_validation():
    use_case, _ = make_use_case(setembro=True)
    with pytest.raises(ValueError, match="user_id"):
        use_case.execute(user_id="")