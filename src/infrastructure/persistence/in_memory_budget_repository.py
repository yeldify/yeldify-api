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

    def list_by_user_id(self, user_id: str, ativo: bool = True) -> List[Budget]:
        """Return budgets for a given user, optionally filtered by active status."""
        result = []
        for budget in self._budgets.values():
            if budget.user_id == user_id and budget.ativo == ativo:
                result.append(budget)
        return result