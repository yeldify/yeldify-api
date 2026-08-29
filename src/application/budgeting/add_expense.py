from src.domain.budgeting.lancamento import Lancamento, TipoLancamento
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository
from datetime import date


class AdicionarDespesaUseCase:
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    def execute(
        self,
        budget_id: str,
        valor: float,
        data: date,
        descricao: str,
        user_id: str,
    ) -> Lancamento:
        # 1. Retrieve budget
        budget = self.budget_repository.get(budget_id)
        if budget is None:
            raise ValueError(f"Budget with id {budget_id} not found")

        # 2. Validate user permission (simplified: budget must belong to user)
        if budget.user_id != user_id:
            raise ValueError("User does not have permission to modify this budget")

        # 3. Validate description non-empty
        if not descricao or not descricao.strip():
            raise ValueError("Description cannot be empty")

        # 4. Create Lancamento domain object (saida)
        lancamento = Lancamento(
            id=self._generate_id(),
            budget_id=budget.id,
            valor=Money(valor, "BRL"),
            data=data,
            descricao=descricao.strip(),
            tipo=TipoLancamento.SAIDA,
        )

        # 5. Add lancamento to budget (updates internal list)
        budget.adicionar_lancamento(lancamento)

        # 6. Save updated budget
        self.budget_repository.save(budget)

        return lancamento

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return str(uuid.uuid4())