import pytest
from decimal import Decimal
from datetime import date, timedelta
from src.domain.budgeting.budget import Budget, TipoLancamento
from src.domain.budgeting.lancamento import Lancamento
from src.domain.budgeting.money import Money
from src.domain.budgeting.exceptions import BudgetInactiveException, BudgetHasTransactionsException


def test_budget_creation():
    budget_id = "budget-1"
    user_id = "user-123"
    nome = "Alimentação"
    categoria = "Essencial"
    start = date(2026, 8, 1)
    end = date(2026, 8, 31)
    limite = Money(Decimal('1000.00'), 'BRL')
    budget = Budget(budget_id, user_id, nome, categoria, start, end, limite)
    assert budget.id == budget_id
    assert budget.user_id == user_id
    assert budget.nome == nome
    assert budget.categoria == categoria
    assert budget.start_date == start
    assert budget.end_date == end
    assert budget.limite == limite
    assert budget.lancamentos == []
    assert budget.ativo is True
    assert budget.saldo == limite  # initial saldo equals limite (no transactions)


def test_budget_adicionar_lancamento_entrada():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    lanc = Lancamento(
        id="lanc-1",
        budget_id=budget.id,
        valor=Money(Decimal('200.00'), 'BRL'),
        data=date(2026, 8, 15),
        descricao="Salário",
        tipo=TipoLancamento.ENTRADA,
    )
    budget.adicionar_lancamento(lanc)
    assert len(budget.lancamentos) == 1
    assert budget.lancamentos[0] == lanc
    # saldo = limite + entrada = 1000 + 200 = 1200
    assert budget.saldo == Money(Decimal('1200.00'), 'BRL')


def test_budget_adicionar_lancamento_saida():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    lanc = Lancamento(
        id="lanc-1",
        budget_id=budget.id,
        valor=Money(Decimal('200.00'), 'BRL'),
        data=date(2026, 8, 15),
        descricao="Supermercado",
        tipo=TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    assert len(budget.lancamentos) == 1
    # saldo = limite - saida = 1000 - 200 = 800
    assert budget.saldo == Money(Decimal('800.00'), 'BRL')


def test_budget_multiple_lancamentos():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    entradas = [
        Lancamento("e1", budget.id, Money(Decimal('500.00'), 'BRL'), date(2026, 8, 5), "Salário", TipoLancamento.ENTRADA),
        Lancamento("e2", budget.id, Money(Decimal('300.00'), 'BRL'), date(2026, 8, 10), "Freelance", TipoLancamento.ENTRADA),
    ]
    saidas = [
        Lancamento("s1", budget.id, Money(Decimal('200.00'), 'BRL'), date(2026, 8, 15), "Supermercado", TipoLancamento.SAIDA),
        Lancamento("s2", budget.id, Money(Decimal('100.00'), 'BRL'), date(2026, 8, 20), "Transporte", TipoLancamento.SAIDA),
    ]
    for lanc in entradas + saidas:
        budget.adicionar_lancamento(lanc)
    assert len(budget.lancamentos) == 4
    # total entradas = 800, total saidas = 300, saldo = limite + 800 - 300 = 1000 + 500 = 1500
    assert budget.saldo == Money(Decimal('1500.00'), 'BRL')


def test_budget_allow_negative_saldo():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('100.00'), 'BRL')
    )
    lanc = Lancamento(
        "lanc-1",
        budget.id,
        Money(Decimal('150.00'), 'BRL'),
        date(2026, 8, 15),
        "Emergency",
        TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    # saldo = 100 - 150 = -50
    assert budget.saldo == Money(Decimal('-50.00'), 'BRL')


def test_budget_lancamento_mismatched_budget_id_raises():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    lanc = Lancamento(
        "lanc-1",
        "budget-2",  # different budget id
        Money(Decimal('50.00'), 'BRL'),
        date(2026, 8, 15),
        "Test",
        TipoLancamento.SAIDA,
    )
    with pytest.raises(ValueError, match="Lancamento budget_id must match Budget's id"):
        budget.adicionar_lancamento(lanc)


def test_budget_desativar_sem_lancamentos():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    assert budget.ativo is True
    budget.desativar()
    assert budget.ativo is False


def test_budget_desativar_com_lancamentos_levanta_excecao():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    lanc = Lancamento(
        "lanc-1",
        budget.id,
        Money(Decimal('100.00'), 'BRL'),
        date(2026, 8, 15),
        "Test",
        TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    with pytest.raises(BudgetHasTransactionsException):
        budget.desativar(data=date(2026, 8, 15))


def test_budget_ativo_falso_nao_aceita_lancamentos():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    budget.desativar()  # now inactive
    lanc = Lancamento(
        "lanc-1",
        budget.id,
        Money(Decimal('50.00'), 'BRL'),
        date(2026, 8, 15),
        "Test",
        TipoLancamento.SAIDA,
    )
    with pytest.raises(BudgetInactiveException):
        budget.adicionar_lancamento(lanc)


def test_budget_pode_ser_desativado_fora_validade():
    # Budget expired (end_date in past)
    past = date(2026, 7, 1)
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 6, 1),
        past,
        Money(Decimal('1000.00'), 'BRL')
    )
    # Add a transaction (still allowed? Actually, if expired, should not be able to add? Spec says desativado nao pode receber mais transações, but expired orcamento may still be active? We'll assume you can still add while active even if past? The spec about validity is for deactivation rule only.)
    # We'll just test that pode_ser_desativado returns True even with lancamentos because outside validity.
    lanc = Lancamento(
        "lanc-1",
        budget.id,
        Money(Decimal('100.00'), 'BRL'),
        date(2026, 6, 15),
        "Test",
        TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    # Orçamento expirado pode ser arquivado mesmo com movimentações.
    date_apos_validade = date(2026, 9, 10)
    assert budget.pode_ser_desativado(date_apos_validade) is True  # because expired


def test_budget_desativar_expirado_com_lancamentos_success():
    # Budget expired (end_date in past) com movimentações pode ser arquivado.
    budget = Budget(
        "budget-1",
        "user-123",
        "Viagem",
        "Lazer",
        date(2026, 6, 1),
        date(2026, 6, 30),
        Money(Decimal('1000.00'), 'BRL')
    )
    lanc = Lancamento(
        "lanc-1",
        budget.id,
        Money(Decimal('100.00'), 'BRL'),
        date(2026, 6, 15),
        "Test",
        TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    assert budget.ativo is True
    budget.desativar(data=date(2026, 9, 10))
    assert budget.ativo is False


def test_budget_pode_ser_desativado_dentro_validade_sem_lancamentos():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    # no lancamentos, dentro da validade => pode arquivar
    assert budget.pode_ser_desativado(date(2026, 8, 15)) is True


def test_budget_nao_pode_ser_desativado_dentro_validade_com_lancamentos():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    lanc = Lancamento(
        "lanc-1",
        budget.id,
        Money(Decimal('100.00'), 'BRL'),
        date(2026, 8, 15),
        "Test",
        TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    # dentro da validade e tem lancamentos => não pode arquivar
    assert budget.pode_ser_desativado(date(2026, 8, 15)) is False


def test_budget_gasto_soma_apenas_saidas():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 8, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    budget.adicionar_lancamento(Lancamento(
        "lanc-1", budget.id, Money(Decimal('100.00'), 'BRL'),
        date(2026, 8, 15), "Saída A", TipoLancamento.SAIDA,
    ))
    budget.adicionar_lancamento(Lancamento(
        "lanc-2", budget.id, Money(Decimal('50.00'), 'BRL'),
        date(2026, 8, 16), "Saída B", TipoLancamento.SAIDA,
    ))
    budget.adicionar_lancamento(Lancamento(
        "lanc-3", budget.id, Money(Decimal('200.00'), 'BRL'),
        date(2026, 8, 17), "Entrada", TipoLancamento.ENTRADA,
    ))
    assert budget.gasto == Money(Decimal('150.00'), 'BRL')
    assert budget.saldo == Money(Decimal('1050.00'), 'BRL')  # 1000 + 200 - 150


def test_budget_gasto_no_periodo_filtra_por_data():
    budget = Budget(
        "budget-1",
        "user-123",
        "Alimentação",
        "Essencial",
        date(2026, 8, 1),
        date(2026, 12, 31),
        Money(Decimal('1000.00'), 'BRL')
    )
    budget.adicionar_lancamento(Lancamento(
        "lanc-1", budget.id, Money(Decimal('100.00'), 'BRL'),
        date(2026, 8, 15), "Em agosto", TipoLancamento.SAIDA,
    ))
    budget.adicionar_lancamento(Lancamento(
        "lanc-2", budget.id, Money(Decimal('40.00'), 'BRL'),
        date(2026, 9, 10), "Em setembro", TipoLancamento.SAIDA,
    ))
    budget.adicionar_lancamento(Lancamento(
        "lanc-3", budget.id, Money(Decimal('30.00'), 'BRL'),
        date(2026, 9, 11), "Receita em setembro", TipoLancamento.ENTRADA,
    ))
    inicio, fim = date(2026, 9, 1), date(2026, 10, 1)
    assert budget.gasto_no_periodo(inicio, fim) == Money(Decimal('40.00'), 'BRL')
    assert budget.receita_no_periodo(inicio, fim) == Money(Decimal('30.00'), 'BRL')