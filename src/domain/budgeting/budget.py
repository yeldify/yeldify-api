from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento
from src.domain.budgeting.exceptions import BudgetInactiveException, BudgetHasTransactionsException


@dataclass
class Budget:
    id: str
    user_id: str
    nome: str
    categoria: str
    start_date: date
    end_date: date
    limite: Money
    _ativo: bool = True
    lancamentos: list[Lancamento] = field(default_factory=list)
    created_at: date = field(default_factory=date.today)

    def __post_init__(self):
        if not self.id or not isinstance(self.id, str):
            raise ValueError("budget_id must be a non-empty string")
        if not self.user_id or not isinstance(self.user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if not self.nome or not isinstance(self.nome, str):
            raise ValueError("nome must be a non-empty string")
        if not self.categoria or not isinstance(self.categoria, str):
            raise ValueError("categoria must be a non-empty string")
        if not isinstance(self.start_date, date):
            raise ValueError("start_date must be a date instance")
        if not isinstance(self.end_date, date):
            raise ValueError("end_date must be a date instance")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        if not isinstance(self.limite, Money):
            raise ValueError("limite must be a Money instance")
        if not isinstance(self.created_at, date):
            raise ValueError("created_at must be a date instance")

    @property
    def ativo(self) -> bool:
        return self._ativo

    def ativar(self) -> None:
        self._ativo = True

    def desativar(self, data: Optional[date] = None) -> None:
        # Rule: dentro da validade, só pode arquivar sem lançamentos;
        # expirado pode ser arquivado mesmo com movimentações.
        if self.lancamentos and self.esta_no_periodo_validade(data or date.today()):
            raise BudgetHasTransactionsException(
                "Não é possível arquivar um orçamento com movimentações dentro da validade. "
                "Mova as transações para outro orçamento antes de arquivar."
            )
        self._ativo = False

    def adicionar_lancamento(self, lancamento: Lancamento) -> None:
        if not self._ativo:
            raise BudgetInactiveException("Cannot add transactions to an inactive budget")
        if lancamento.budget_id != self.id:
            raise ValueError("Lancamento budget_id must match Budget's id")
        self.lancamentos.append(lancamento)

    @property
    def saldo(self) -> Money:
        total = Money(Decimal('0'), self.limite.currency)
        for lanc in self.lancamentos:
            if lanc.tipo == TipoLancamento.ENTRADA:
                total += lanc.valor
            else:  # SAIDA
                total -= lanc.valor
        return self.limite + total  # limite + (entradas - saídas)

    @property
    def gasto(self) -> Money:
        """Sum of SAIDA lancamentos (expenses)."""
        total = Money(Decimal('0'), self.limite.currency)
        for lanc in self.lancamentos:
            if lanc.tipo == TipoLancamento.SAIDA:
                total += lanc.valor
        return total

    def gasto_no_periodo(self, inicio: date, fim: date) -> Money:
        """Sum of SAIDA lancamentos whose `data` falls within [inicio, fim) range."""
        total = Money(Decimal('0'), self.limite.currency)
        for lanc in self.lancamentos:
            if lanc.tipo == TipoLancamento.SAIDA and inicio <= lanc.data < fim:
                total += lanc.valor
        return total

    def receita_no_periodo(self, inicio: date, fim: date) -> Money:
        """Sum of ENTRADA lancamentos whose `data` falls within [inicio, fim) range."""
        total = Money(Decimal('0'), self.limite.currency)
        for lanc in self.lancamentos:
            if lanc.tipo == TipoLancamento.ENTRADA and inicio <= lanc.data < fim:
                total += lanc.valor
        return total

    def esta_no_periodo_validade(self, data: date) -> bool:
        return self.start_date <= data <= self.end_date

    def pode_ser_desativado(self, data: date) -> bool:
        """
        According to spec:
        - Orçamentos que estiverem dentro da validade, só poderão ser desativados,
          após usuário designar as transações para outro orçamento
        Means: if budget is still valid (within start/end date), you can only deactivate
        after moving transactions elsewhere. So we check if there are any lancamentos;
        if yes, cannot deactivate unless they have been reassigned (we cannot know
        reassignment here, so we just rely on the desativar method which checks
        lancamentos list empty).
        For budgets outside validity (expired), they can be deactivated regardless?
        Spec says: "Orçamentos que estiverem dentro da validade, só poderão ser desativados,
          após usuário designar as transações para outro orçamento"
        So if outside validity (expired), they can be deactivated even with transactions?
        We'll implement: can deactivate if (not within validity) or (no lancamentos).
        """
        if not self.esta_no_periodo_validade(data):
            return True  # expired budgets can be deactivated anytime
        return len(self.lancamentos) == 0