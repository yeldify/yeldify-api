from typing import Generator
from fastapi import Depends
from src.application.budgeting.add_expense import AdicionarDespesaUseCase
from src.application.budgeting.add_receita import AdicionarReceitaUseCase
from src.application.budgeting.list_orcamentos import ListarOrcamentosUseCase
from src.application.budgeting.editar_orcamento import EditarOrcamentoUseCase
from src.application.budgeting.criar_orcamento import CriarOrcamentoUseCase
from src.application.budgeting.listar_transacoes import ListarTransacoesUseCase
from src.application.budgeting.editar_transacao import EditarTransacaoUseCase
from src.application.budgeting.dashboard_micro import DashboardMicroUseCase
from src.infrastructure.persistence.repositories import IBudgetRepository
from src.infrastructure.persistence.repository_factory import create_repository


def get_budget_repository() -> Generator[IBudgetRepository, None, None]:
    """Provide a repository instance (InMemory or PostgreSQL based on USE_POSTGRES env var)."""
    repo = create_repository()
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


def get_criar_orcamento_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> CriarOrcamentoUseCase:
    """Provide the criar orcamento use case with its repository injected."""
    return CriarOrcamentoUseCase(budget_repository=repo)


def get_adicionar_receita_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> AdicionarReceitaUseCase:
    """Provide the adicionar receita use case with its repository injected."""
    return AdicionarReceitaUseCase(budget_repository=repo)


def get_listar_transacoes_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> ListarTransacoesUseCase:
    """Provide the listar transações use case with its repository injected."""
    return ListarTransacoesUseCase(budget_repository=repo)


def get_editar_transacao_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> EditarTransacaoUseCase:
    """Provide the editar transação use case with its repository injected."""
    return EditarTransacaoUseCase(budget_repository=repo)


def get_dashboard_micro_use_case(
    repo: IBudgetRepository = Depends(get_budget_repository)
) -> DashboardMicroUseCase:
    """Provide the dashboard micro use case with its repository injected."""
    return DashboardMicroUseCase(
        budget_repository=repo,
        listar_transacoes_use_case=ListarTransacoesUseCase(budget_repository=repo),
    )