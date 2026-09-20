"""
Use case for adding income/revenue to a budget.
"""
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento, MetodoPagamento
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository
from datetime import date
from typing import Optional


class AdicionarReceitaUseCase:
    """
    Use case to add income (ENTRADA) to a budget.
    """
    
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository
    
    def execute(
        self,
        budget_id: str,
        valor: float,
        data: date,
        descricao: str,
        categoria: str,
        user_id: str,
        conta: Optional[str] = None,
        metodo_pagamento: Optional[MetodoPagamento] = None,
        pendente: bool = False,
    ) -> Lancamento:
        """
        Add an income transaction (ENTRADA) to a budget.
        
        Args:
            budget_id: ID of the budget to add income to
            valor: Income amount (positive value in BRL)
            data: Date the income was received
            descricao: Description of the income
            categoria: Category of the income (e.g., "Salário", "Freelance", "Investimentos")
            user_id: ID of the user
            conta: Account label (e.g., "Itaú • Conta Corrente")
            metodo_pagamento: Payment method (metodo)
            pendente: Whether the transaction still needs classification
            
        Returns:
            Lancamento: The created income transaction
            
        Raises:
            ValueError: If budget not found, user doesn't have permission, or invalid values
        """
        # 1. Validate valor is positive
        if valor <= 0:
            raise ValueError("Valor da receita deve ser maior que zero")
        
        # 2. Retrieve budget
        budget = self.budget_repository.get(budget_id)
        if budget is None:
            raise ValueError(f"Budget with id {budget_id} not found")

        # 3. Validate user permission
        if budget.user_id != user_id:
            raise ValueError("User does not have permission to modify this budget")

        # 4. Validate description non-empty
        if not descricao or not descricao.strip():
            raise ValueError("Description cannot be empty")
        
        # 5. Validate categoria non-empty
        if not categoria or not categoria.strip():
            raise ValueError("Categoria cannot be empty")

        # 6. Validate conta and metodo_pagamento
        if conta is not None and (not conta or not str(conta).strip()):
            raise ValueError("Conta cannot be empty")
        effective_conta = str(conta).strip() if conta is not None else "Não informada"
        effective_metodo = metodo_pagamento if metodo_pagamento is not None else MetodoPagamento.OUTROS

        # 7. Create Lancamento domain object (ENTRADA = income)
        lancamento = Lancamento(
            id=self._generate_id(),
            budget_id=budget_id,
            valor=Money(valor, "BRL"),
            data=data,
            descricao=descricao.strip(),
            tipo=TipoLancamento.ENTRADA,
            categoria=categoria.strip(),
            conta=effective_conta,
            metodo_pagamento=effective_metodo,
            pendente=pendente,
        )

        # 8. Add lancamento to budget (updates internal list)
        budget.adicionar_lancamento(lancamento)

        # 9. Save updated budget
        self.budget_repository.save(budget)

        return lancamento
    
    @staticmethod
    def _generate_id() -> str:
        import uuid
        return str(uuid.uuid4())
