from __future__ import annotations
from datetime import date, timedelta
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository


class CriarOrcamentoUseCase:
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    def execute(
        self,
        nome: str,
        categoria: str,
        valor: float,
        validade_meses: int,
        user_id: str,
    ) -> Budget:
        """
        Cria um novo orçamento.

        Args:
            nome: nome do orçamento (ex: "Alimentação")
            categoria: categoria do orçamento (ex: "Essencial")
            valor: limite do orçamento (em BRL)
            validade_meses: deve ser um de [1, 2, 3, 6, 9, 12]
            user_id: ID do usuário logado

        Returns:
            Budget: o orçamento criado
        """
        # 1. Validate inputs
        if not nome or not isinstance(nome, str):
            raise ValueError("nome must be a non-empty string")
        if not categoria or not isinstance(categoria, str):
            raise ValueError("categoria must be a non-empty string")
        if valor <= 0:
            raise ValueError("valor must be positive")
        if validade_meses not in [1, 2, 3, 6, 9, 12]:
            raise ValueError("validade_meses must be one of [1, 2, 3, 6, 9, 12]")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")

        # 2. Calculate dates
        start_date = date.today()
        # Approximate month as 30 days; for production use relativedelta or calendar
        end_date = start_date + timedelta(days=30 * validade_meses)

        # 3. Create Budget entity
        budget = Budget(
            id=self._generate_id(),
            user_id=user_id,
            nome=nome,
            categoria=categoria,
            start_date=start_date,
            end_date=end_date,
            limite=Money(valor, "BRL"),  # assuming BRL for now
        )

        # 4. Persist
        self.budget_repository.save(budget)

        return budget

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return str(uuid.uuid4())