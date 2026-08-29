from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from src.domain.budgeting.money import Money


@dataclass(frozen=True)
class Expense:
    id: str
    budget_id: str
    valor: Money
    data: date
    descricao: str

    def __post_init__(self):
        # Validate ids
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Expense id must be a non-empty string")
        if not isinstance(self.budget_id, str) or not self.budget_id.strip():
            raise ValueError("Budget id must be a non-empty string")
        # Validate description
        if not isinstance(self.descricao, str) or not self.descricao.strip():
            raise ValueError("Description must be a non-empty string")
        # Validate data is a date instance (should be, but just in case)
        if not isinstance(self.data, date):
            raise ValueError("Data must be a date instance")
        # Money validation already ensures valor.amount is Decimal and currency non-empty
        # Expense amount must be positive
        if self.valor.amount <= Decimal('0'):
            raise ValueError("Expense amount must be positive")