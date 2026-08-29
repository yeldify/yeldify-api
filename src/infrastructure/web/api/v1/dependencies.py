from typing import Generator
from fastapi import Depends
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.application.budgeting.add_expense import AdicionarDespesaUseCase
from src.application.budgeting.list_orcamentos import ListarOrcamentosUseCase
from src.application.budgeting.editar_orcamento import EditarOrcamentoUseCase
from src.infrastructure.persistence.repositories import IBudgetRepository


def get_budget_repository() -> Generator[IBudgetRepository, None, None]:
    """Provide a repository instance (in‑memory for now)."""
    repo = InMemoryBudgetRepository()
    try:
        yield repo
    finally:
        pass  # nothing to clean up


def get_adicionar_despesa_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> AdicionarDespesaUseCase:
    """Provide the use case with its repository injected."""
    return AdicionarDespesaUseCase(budget_repository=repo)


def get_listar_orcamentos_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> ListarOrcamentosUseCase:
    """Provide the listar orçamentos use case with its repository injected."""
    return ListarOrcamentosUseCase(budget_repository=repo)


def get_editar_orcamento_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> EditarOrcamentoUseCase:
    """Provide the editar orcamento use case with its repository injected."""
    return EditarOrcamentoUseCase(budget_repository=repo)