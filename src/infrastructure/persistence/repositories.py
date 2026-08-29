from abc import ABC, abstractmethod
from src.domain.budgeting.budget import Budget
from typing import List, Optional


class IBudgetRepository(ABC):
    @abstractmethod
    def get(self, budget_id: str) -> Budget | None:
        """Retrieve a budget by its ID."""
        ...

    @abstractmethod
    def save(self, budget: Budget) -> None:
        """Save a budget."""
        ...

    @abstractmethod
    def list_by_user_id(
        self, user_id: str, ativo: Optional[bool] = True
    ) -> List[Budget]:
        """
        List budgets for a given user.
        If ativo is True, return only active budgets.
        If ativo is False, return only inactive budgets.
        If ativo is None, return all budgets (active and inactive).
        """
        ...