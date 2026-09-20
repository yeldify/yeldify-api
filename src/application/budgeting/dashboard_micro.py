from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from src.application.budgeting.listar_transacoes import (
    ListarTransacoesUseCase,
    TransacaoResult,
    parse_ano_mes,
)
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository


# Percentual do teto a partir do qual o orçamento é marcado como "atenção".
ATENCAO_PERCENTUAL = 80.0
# Percentual do teto a partir do qual o orçamento é marcado como "estourado".
ESTOURADO_PERCENTUAL = 100.0


@dataclass(frozen=True)
class ResumoMicro:
    saldo_disponivel: float
    total_receitas: float
    total_despesas: float
    qtd_orcamentos_ativos: int


@dataclass(frozen=True)
class OrcamentoStatusItem:
    id: str
    nome: str
    categoria: str
    teto: float
    gasto: float
    percentual: float
    status: str


@dataclass(frozen=True)
class DesvioItem:
    budget_id: str
    nome: str
    percentual: float
    excedente: float
    dias_restantes: int


@dataclass(frozen=True)
class DashboardMicroResult:
    resumo: ResumoMicro
    orcamentos: List[OrcamentoStatusItem]
    desvios: List[DesvioItem]
    transacoes_recentes: List[TransacaoResult]


class DashboardMicroUseCase:
    def __init__(
        self,
        budget_repository: IBudgetRepository,
        listar_transacoes_use_case: ListarTransacoesUseCase,
    ):
        self.budget_repository = budget_repository
        self.listar_transacoes_use_case = listar_transacoes_use_case

    def execute(self, user_id: str, ano_mes: Optional[str] = None) -> DashboardMicroResult:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")

        if ano_mes is None:
            hoje = date.today()
            ano_mes = f"{hoje.year:04d}-{hoje.month:02d}"

        inicio, fim = parse_ano_mes(ano_mes)
        hoje = date.today()

        budgets = self.budget_repository.list_by_user_id(user_id, ativo=True)

        total_receitas = Money.from_string(0, "BRL")
        total_despesas = Money.from_string(0, "BRL")
        orcamentos: List[OrcamentoStatusItem] = []
        desvios: List[DesvioItem] = []

        for budget in budgets:
            gasto = budget.gasto_no_periodo(inicio, fim)
            receita = budget.receita_no_periodo(inicio, fim)
            total_despesas += gasto
            total_receitas += receita

            teto = float(budget.limite.amount)
            gasto_valor = float(gasto.amount)
            percentual = (gasto_valor / teto * 100) if teto > 0 else 0.0

            if percentual > ESTOURADO_PERCENTUAL:
                status = "estourado"
            elif percentual >= ATENCAO_PERCENTUAL:
                status = "atencao"
            else:
                status = "ok"

            orcamentos.append(
                OrcamentoStatusItem(
                    id=budget.id,
                    nome=budget.nome,
                    categoria=budget.categoria,
                    teto=teto,
                    gasto=gasto_valor,
                    percentual=round(percentual, 1),
                    status=status,
                )
            )

            if status != "ok":
                desvios.append(
                    DesvioItem(
                        budget_id=budget.id,
                        nome=budget.nome,
                        percentual=round(percentual, 1),
                        excedente=max(gasto_valor - teto, 0.0),
                        dias_restantes=max((fim - hoje).days, 0),
                    )
                )

        desvios.sort(key=lambda d: d.percentual, reverse=True)

        transacoes_recentes, _ = self.listar_transacoes_use_case.execute(
            user_id=user_id,
            ano_mes=ano_mes,
            page=1,
            page_size=7,
        )

        saldo = total_receitas - total_despesas

        return DashboardMicroResult(
            resumo=ResumoMicro(
                saldo_disponivel=float(saldo.amount),
                total_receitas=float(total_receitas.amount),
                total_despesas=float(total_despesas.amount),
                qtd_orcamentos_ativos=len(budgets),
            ),
            orcamentos=orcamentos,
            desvios=desvios,
            transacoes_recentes=transacoes_recentes,
        )