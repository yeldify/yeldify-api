import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from src.application.budgeting.add_expense import AdicionarDespesaUseCase
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.expense import Expense
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


def test_adicionar_despesa_success():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    # setup budget
    budget = Budget(
        budget_id="budget-1",
        user_id="user-123",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        limite=Money(Decimal('1000.00'), 'BRL')
    )
    repo.budgets[budget.id] = budget

    # execute
    expense = use_case.execute(
        budget_id="budget-1",
        valor=Decimal('200.00'),
        data=date(2026, 8, 15),
        descricao="Supermercado",
        user_id="user-123"
    )

    # assertions
    assert isinstance(expense, Expense)
    assert expense.budget_id == "budget-1"
    assert expense.valor == Money(Decimal('200.00'), 'BRL')
    assert expense.descricao == "Supermercado"
    assert expense.data == date(2026, 8, 15)

    # budget should have expense
    updated_budget = repo.get("budget-1")
    assert len(updated_budget.despesas) == 1
    assert updated_budget.saldo == Money(Decimal('800.00'), 'BRL')
    # save should have been called
    assert len(repo.saved) == 1


def test_adicionar_despesa_budget_not_found():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    with pytest.raises(ValueError, match="Budget with id budget-999 not found"):
        use_case.execute(
            budget_id="budget-999",
            valor=Decimal('50'),
            data=date.today(),
            descricao="Test",
            user_id="user-123"
        )


def test_adicionar_despesa_wrong_user():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    budget = Budget(
        budget_id="budget-1",
        user_id="user-123",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        limite=Money(Decimal('500.00'), 'BRL')
    )
    repo.budgets[budget.id] = budget

    with pytest.raises(ValueError, match="User does not have permission"):
        use_case.execute(
            budget_id="budget-1",
            valor=Decimal('100'),
            data=date.today(),
            descricao="Test",
            user_id="different-user"
        )


def test_adicionar_despesa_empty_description():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    budget = Budget(
        budget_id="budget-1",
        user_id="user-123",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        limite=Money(Decimal('500.00'), 'BRL')
    )
    repo.budgets[budget.id] = budget

    with pytest.raises(ValueError, match="Description cannot be empty"):
        use_case.execute(
            budget_id="budget-1",
            valor=Decimal('30'),
            data=date.today(),
            descricao="   ",
            user_id="user-123"
        )


def test_adicionar_despesa_negative_valor():
    repo = FakeBudgetRepository()
    use_case = AdicionarDespesaUseCase(repo)

    budget = Budget(
        budget_id="budget-1",
        user_id="user-123",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        limite=Money(Decimal('500.00'), 'BRL')
    )
    repo.budgets[budget.id] = budget

    with pytest.raises(ValueError):
        use_case.execute(
            budget_id="budget-1",
            valor=Decimal('-10'),
            data=date.today(),
            descricao="Test",
            user_id="user-123"
        )