import pytest
from decimal import Decimal, InvalidOperation
from src.domain.budgeting.money import Money

def test_money_creation_with_valid_amount():
    money = Money(Decimal('10.50'), 'BRL')
    assert money.amount == Decimal('10.50')
    assert money.currency == 'BRL'

def test_money_zero_allowed():
    money = Money(Decimal('0'), 'BRL')
    assert money.amount == Decimal('0')

def test_money_negative_amount_raises():
    with pytest.raises(ValueError):
        Money(Decimal('-5.00'), 'BRL')

def test_money_immutable_after_creation():
    money = Money(Decimal('100'), 'USD')
    # amount and currency should be read-only (if using properties)
    assert money.amount == Decimal('100')
    assert money.currency == 'USD'
    # Attempt to modify should raise AttributeError if using @property without setter
    with pytest.raises(AttributeError):
        money.amount = Decimal('200')
    with pytest.raises(AttributeError):
        money.currency = 'EUR'

def test_money_equality():
    m1 = Money(Decimal('50'), 'BRL')
    m2 = Money(Decimal('50'), 'BRL')
    m3 = Money(Decimal('50'), 'USD')
    assert m1 == m2
    assert m1 != m3

def test_money_addition():
    m1 = Money(Decimal('10'), 'BRL')
    m2 = Money(Decimal('20'), 'BRL')
    result = m1 + m2
    assert isinstance(result, Money)
    assert result.amount == Decimal('30')
    assert result.currency == 'BRL'

def test_money_subtraction():
    m1 = Money(Decimal('30'), 'BRL')
    m2 = Money(Decimal('10'), 'BRL')
    result = m1 - m2
    assert result.amount == Decimal('20')

def test_money_operations_different_currency_raises():
    m1 = Money(Decimal('10'), 'BRL')
    m2 = Money(Decimal('10'), 'USD')
    with pytest.raises(ValueError):
        _ = m1 + m2
    with pytest.raises(ValueError):
        _ = m1 - m2

def test_money_from_string():
    money = Money.from_string('123.45', 'BRL')
    assert money.amount == Decimal('123.45')
    assert money.currency == 'BRL'

def test_money_from_string_invalid_raises():
    with pytest.raises(ValueError):
        Money.from_string('abc', 'BRL')