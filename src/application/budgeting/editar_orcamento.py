from __future__ import annotations
from datetime import date, timedelta
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.exceptions import BudgetInactiveException, BudgetHasTransactionsException
from src.infrastructure.persistence.repositories import IBudgetRepository


class EditarOrcamentoUseCase:
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    VALID_VALIDADE_MESES = {1, 2, 3, 6, 9, 12}

    def execute(
        self,
        budget_id: str,
        user_id: str,
        nome: str | None = None,
        valor: float | None = None,
        validade_meses: int | None = None,
        ativo: bool | None = None,
        nota_governanca: str | None = None,
    ) -> Budget:
        """
        Edit an active budget.
        Only fields provided (not None) are updated.
        """
        # 1. Retrieve budget
        budget = self.budget_repository.get(budget_id)
        if budget is None:
            raise ValueError(f"Budget with id {budget_id} not found")

        # 2. Validate user permission (simplified: budget must belong to user)
        if budget.user_id != user_id:
            raise ValueError("User does not have permission to modify this budget")

        # 3. Apply changes and validate
        changes_made = False

        if nome is not None:
            if not nome or not nome.strip():
                raise ValueError("Campo vazio. Informe nome")
            # Check duplicate name per user (excluding current budget)
            duplicate = self._budget_with_same_name_exists(
                user_id=user_id, nome=nome.strip(), exclude_id=budget_id
            )
            if duplicate:
                raise ValueError("Já existe um orçamento com este nome")
            budget.nome = nome.strip()
            changes_made = True

        if valor is not None:
            # valor is the limite (planned value)
            if valor < 0:
                raise ValueError("Valor do orçamento não pode ser menor que zero")
            # Governance: alterar o teto de um orçamento com movimentações exige justificativa
            if budget.lancamentos and not nota_governanca:
                raise ValueError(
                    "Justificativa obrigatória para alterar orçamento com movimentações."
                )
            # Ensure it's a Money object with same currency
            # We'll keep the same currency as existing limit (assuming BRL for now)
            budget.limite = Money(valor, budget.limite.currency)
            changes_made = True

        if validade_meses is not None:
            # Validity editing rules
            if validade_meses not in self.VALID_VALIDADE_MESES:
                raise ValueError(
                    "Validade deve ser um dos valores: 1, 2, 3, 6, 9 ou 12 meses."
                )
            # Cannot edit validity if budget already expired
            if not budget.esta_no_periodo_validade(date.today()):
                raise ValueError(
                    "Não é possível editar a validade de um orçamento expirado."
                )
            # Recalculate endDate from today (date of edit)
            new_end_date = date.today() + timedelta(days=30 * validade_meses)
            budget.end_date = new_end_date
            changes_made = True

        if ativo is not None:
            if ativo:
                try:
                    budget.ativar()
                except Exception as e:
                    # Should not happen, but just in case
                    raise ValueError(str(e)) from e
            else:
                try:
                    budget.desativar()
                except (BudgetInactiveException, BudgetHasTransactionsException) as e:
                    raise ValueError(str(e)) from e
                except Exception as e:
                    raise ValueError(str(e)) from e
            changes_made = True

        if nota_governanca is not None:
            nota = nota_governanca.strip()
            if not nota:
                raise ValueError("Justificativa não pode ser vazia.")
            budget.nota_governanca = nota
            changes_made = True

        # If no changes, just return budget (or could raise? but we'll return)
        if not changes_made:
            return budget

        # Additional validation after changes: ensure startDate <= endDate (should hold)
        if budget.start_date > budget.end_date:
            raise ValueError("Data de início não pode ser após data de término")

        # Save updated budget
        self.budget_repository.save(budget)
        return budget

    def _budget_with_same_name_exists(
        self, user_id: str, nome: str, exclude_id: str
    ) -> bool:
        """
        Check if there is another budget (any status) with same name for user.
        Spec: "Não pode haver 2 orçamentos com mesmo nome"
        """
        budgets = self.budget_repository.list_by_user_id(user_id, ativo=None)
        for b in budgets:
            if b.id == exclude_id:
                continue
            if b.nome == nome:
                return True
        return False