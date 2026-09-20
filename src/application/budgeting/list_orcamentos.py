from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from src.domain.budgeting.budget import Budget
from src.infrastructure.persistence.repositories import IBudgetRepository


@dataclass(frozen=True)
class PaginatedOrcamentos:
    items: List[Budget]
    total: int


class ListarOrcamentosUseCase:
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    def execute(
        self,
        user_id: str,
        *,
        sort_by: str = "nome",
        ativo: Optional[bool] = True,
        page: int = 1,
        page_size: int = 10,
    ) -> List[Budget]:
        """
        Lista orçamentos de um usuário com ordenação e paginação.

        Args:
            user_id: ID do usuário logado.
            sort_by: Campo pelo qual ordenar. Valores aceitos: 
                'nome' (ordem alfabética), 'valor_restante' (saldo), 
                'valor_planejado' (limite), 'data_criacao' (created_at).
                Padrão: 'nome'.
            ativo: Filtro pelo status. True para ativos (padrão), False para
                arquivados/inativos e None para todos.
            page: Número da página (começando em 1). Padrão: 1.
            page_size: Quantidade de itens por página. Padrão: 10.

        Returns:
            PaginatedOrcamentos com a lista de objetos Budget já ordenados e
            paginados, e o total de itens antes da paginação.
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1:
            raise ValueError("page_size must be >= 1")

        # Obter orçamentos do usuário (ativo pode ser True/False/None)
        budgets = self.budget_repository.list_by_user_id(user_id, ativo=ativo)

        # Função de chave para ordenação
        def get_key(b: Budget):
            if sort_by == "nome":
                return b.nome.lower()
            elif sort_by == "valor_restante":
                return b.saldo.amount  # Money.amount is Decimal
            elif sort_by == "valor_planejado":
                return b.limite.amount
            elif sort_by == "data_criacao":
                return b.created_at
            else:
                # fallback to nome
                return b.nome.lower()

        # Ordenar
        sorted_budgets = sorted(budgets, key=get_key)

        # Total antes da paginação
        total = len(sorted_budgets)

        # Paginação
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated = sorted_budgets[start_index:end_index]

        return PaginatedOrcamentos(items=paginated, total=total)