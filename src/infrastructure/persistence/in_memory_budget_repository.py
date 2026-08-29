from typing import Dict, Optional, List
from src.domain.budgeting.budget import Budget
from src.infrastructure.persistence.repositories import IBudgetRepository


class InMemoryBudgetRepository(IBudgetRepository):
    """Simple in‑memory repository for Budget aggregates."""
    def __init__(self):
        self._budgets: Dict[str, Budget] = {}

    def get(self, budget_id: str) -> Optional[Budget]:
        return self._budgets.get(budget_id)

    def save(self, budget: Budget) -> None:
        self._budgets[budget.id] = budget

    def list_by_user_id(
        self, user_id: str, ativo: Optional[bool] = True
    ) -> List[Budget]:
        """
        Return budgets for a given user.
        If ativo is True, return only active budgets.
        If ativo is False, return only inactive budgets.
        If ativo is None, return all budgets (active and inactive).
        """
        result = []
        for budget in self._budgets.values():
            if budget.user_id != user_id:
                continue
            if ativo is None or budget.ativo == ativo:
                result.append(budget)
        return result