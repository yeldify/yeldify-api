import pytest
from datetime import date
from decimal import Decimal
from typing import List, Optional

from src.application.budgeting.add_expense import AdicionarDespesaUseCase
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento, MetodoPagamento
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository


class FakeBudgetRepository(IBudgetRepository):
    def __init__(self):
        self.budgets = {}
        self.saved = []

    def get(self, budget_id: str):
        return self.budgets.get(budget_id)

    def save(self, budget: Budget) -> None:
        self.saved.append(budget)
        # also keep in dict for subsequent gets
        self.budgets[budget.id] = budget

    def list_by_user_id(
        self, user_id: str, ativo: Optional[bool] = True
    ) -> List[Budget]:
        return [
            b
            for b in self.budgets.values()
            if b.user_id == user_id and (ativo is None or b.ativo == ativo)
        ]


def _make_budget(budget_id: str = "budget-1", user_id: str = "user-123", limite: str = "1000.00"):
    return Budget(
        id=budget_id,
        user_id=user_id,
        nome="Alimentação",
        categoria="Alimentação",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        limite=Money(Decimal(limite), "BRL"),
    )


def test_adicionar_despesa_success():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    budget = _make_budget()
    repo.budgets[budget.id] = budget

    expense = use_case.execute(
        budget_id="budget-1",
        valor=Decimal("200.00"),
        data=date(2026, 8, 15),
        descricao="Supermercado",
        user_id="user-123",
    )

    assert isinstance(expense, Lancamento)
    assert expense.tipo == TipoLancamento.SAIDA
    assert expense.budget_id == "budget-1"
    assert expense.valor == Money(Decimal("200.00"), "BRL")
    assert expense.descricao == "Supermercado"
    assert expense.data == date(2026, 8, 15)
    # defaults for new fields
    assert expense.conta == "Não informada"
    assert expense.metodo_pagamento == MetodoPagamento.OUTROS
    assert expense.pendente is False

    updated_budget = repo.get("budget-1")
    assert len(updated_budget.lancamentos) == 1
    assert updated_budget.saldo == Money(Decimal("800.00"), "BRL")
    assert len(repo.saved) == 1


def test_adicionar_despesa_com_conta_metodo_e_pendente():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)
    repo.budgets["budget-1"] = _make_budget()

    expense = use_case.execute(
        budget_id="budget-1",
        valor=100.0,
        data=date(2026, 8, 15),
        descricao="Uber",
        user_id="user-123",
        categoria="Transporte",
        conta="Cartão Nubank • Crédito",
        metodo_pagamento=MetodoPagamento.CARTAO,
        pendente=True,
    )

    assert expense.categoria == "Transporte"
    assert expense.conta == "Cartão Nubank • Crédito"
    assert expense.metodo_pagamento == MetodoPagamento.CARTAO
    assert expense.pendente is True


def test_adicionar_despesa_conta_em_branco_rejeitada():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)
    repo.budgets["budget-1"] = _make_budget()

    with pytest.raises(ValueError, match="Conta cannot be empty"):
        use_case.execute(
            budget_id="budget-1",
            valor=10.0,
            data=date.today(),
            descricao="Test",
            user_id="user-123",
            conta="   ",
        )


def test_adicionar_despesa_categoria_em_branco_rejeitada():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)
    repo.budgets["budget-1"] = _make_budget()

    with pytest.raises(ValueError, match="Categoria cannot be empty"):
        use_case.execute(
            budget_id="budget-1",
            valor=10.0,
            data=date.today(),
            descricao="Test",
            user_id="user-123",
            categoria="  ",
        )


def test_adicionar_despesa_budget_not_found():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    with pytest.raises(ValueError, match="Budget with id budget-999 not found"):
        use_case.execute(
            budget_id="budget-999",
            valor=Decimal("50"),
            data=date.today(),
            descricao="Test",
            user_id="user-123",
        )


def test_adicionar_despesa_wrong_user():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)
    repo.budgets["budget-1"] = _make_budget(user_id="user-123", limite="500.00")

    with pytest.raises(ValueError, match="User does not have permission"):
        use_case.execute(
            budget_id="budget-1",
            valor=Decimal("100"),
            data=date.today(),
            descricao="Test",
            user_id="different-user",
        )


def test_adicionar_despesa_empty_description():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)
    repo.budgets["budget-1"] = _make_budget(limite="500.00")

    with pytest.raises(ValueError, match="Description cannot be empty"):
        use_case.execute(
            budget_id="budget-1",
            valor=Decimal("30"),
            data=date.today(),
            descricao="   ",
            user_id="user-123",
        )


def test_adicionar_despesa_negative_valor():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)
    repo.budgets["budget-1"] = _make_budget(limite="500.00")

    with pytest.raises(ValueError):
        use_case.execute(
            budget_id="budget-1",
            valor=Decimal("-10"),
            data=date.today(),
            descricao="Test",
            user_id="user-123",
        )
