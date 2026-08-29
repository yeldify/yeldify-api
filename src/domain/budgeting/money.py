from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Union


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, 'amount', Decimal(str(self.amount)))
            except InvalidOperation:
                raise ValueError(f"Invalid amount: {self.amount}")
        if not isinstance(self.currency, str) or not self.currency:
            raise ValueError("Currency must be a non-empty string")
        # Note: amount can be negative, zero, or positive

    @classmethod
    def from_string(cls, value: Union[str, int, float], currency: str) -> 'Money':
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ValueError(f"Cannot convert {value} to Decimal")
        return cls(amount, currency)

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount <= other.amount

    def __gt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount > other.amount

    def __ge__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount >= other.amount

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __repr__(self) -> str:
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"