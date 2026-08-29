from abc import ABC, abstractmethod
from src.domain.budgeting.budget import Budget


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
    def list_by_user_id(self, user_id: str, ativo: bool = True) -> list[Budget]:
        """List budgets for a given user, optionally filtered by active status."""
        ...