import pytest
from decimal import Decimal
from datetime import date
from src.domain.budgeting.expense import Expense
from src.domain.budgeting.money import Money

def test_expense_creation_valid():
    expense_id = "exp-123"
    budget_id = "budget-456"
    valor = Money(Decimal('100.50'), 'BRL')
    data = date(2026, 8, 27)
    descricao = "Supermercado"
    
    expense = Expense(expense_id, budget_id, valor, data, descricao)
    
    assert expense.id == expense_id
    assert expense.budget_id == budget_id
    assert expense.valor == valor
    assert expense.data == data
    assert expense.descricao == descricao

def test_expense_negative_valor_raises():
    with pytest.raises(ValueError):
        Expense(
            "exp-1",
            "budget-1",
            Money(Decimal('-50'), 'BRL'),  # negative amount
            date.today(),
            "Test"
        )

def test_expense_zero_valor_raises():
    with pytest.raises(ValueError):
        Expense(
            "exp-1",
            "budget-1",
            Money(Decimal('0'), 'BRL'),
            date.today(),
            "Test"
        )

def test_expense_future_date_allowed_for_now():
    # For now, we allow future dates; business rule can be added later
    future_date = date(2026, 12, 31)
    expense = Expense(
        "exp-1",
        "budget-1",
        Money(Decimal('100'), 'BRL'),
        future_date,
        "Test"
    )
    assert expense.data == future_date

def test_expense_empty_descricao_raises():
    with pytest.raises(ValueError):
        Expense(
            "exp-1",
            "budget-1",
            Money(Decimal('50'), 'BRL'),
            date.today(),
            ""  # empty description
        )

def test_expense_descricao_whitespace_raises():
    with pytest.raises(ValueError):
        Expense(
            "exp-1",
            "budget-1",
            Money(Decimal('50'), 'BRL'),
            date.today(),
            "   "  # only whitespace
        )

def test_expense_immutability():
    expense = Expense(
        "exp-1",
        "budget-1",
        Money(Decimal('100'), 'BRL'),
        date.today(),
        "Test"
    )
    # Attempt to modify should raise AttributeError (frozen dataclass behavior)
    with pytest.raises(AttributeError):
        expense.id = "exp-2"
    with pytest.raises(AttributeError):
        expense.valor = Money(Decimal('200'), 'BRL')