from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from src.domain.budgeting.lancamento import TipoLancamento
from src.infrastructure.persistence.repositories import IBudgetRepository


@dataclass(frozen=True)
class TransacaoResult:
    id: str
    budget_id: str
    budget_nome: str
    budget_categoria: str
    descricao: str
    valor: float
    data: date
    categoria: str
    tipo: str
    conta: str = "Não informada"
    metodo_pagamento: str = "outros"
    pendente: bool = False


def parse_ano_mes(ano_mes: str) -> Tuple[date, date]:
    """
    Converts "YYYY-MM" into an exclusive [inicio, fim) window.
    """
    try:
        ano, mes = (int(x) for x in ano_mes.split("-"))
        inicio = date(ano, mes, 1)
        fim = date(ano + mes // 12, (mes % 12) + 1, 1)
    except (ValueError, AttributeError):
        raise ValueError("ano_mes must be in format YYYY-MM")
    return inicio, fim


class ListarTransacoesUseCase:
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    def execute(
        self,
        user_id: str,
        *,
        tipo: Optional[str] = None,
        ano_mes: Optional[str] = None,
        budget_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[TransacaoResult], int]:
        """
        Lista todas as transações (lançamentos) do usuário, agregadas a partir
        dos orçamentos, ordenadas por data decrescente.

        Returns:
            Tupla (items, total) já paginada.
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1:
            raise ValueError("page_size must be >= 1")
        if tipo is not None and tipo not in (TipoLancamento.ENTRADA.value, TipoLancamento.SAIDA.value):
            raise ValueError("tipo must be ENTRADA or SAIDA")

        inicio, fim = (None, None)
        if ano_mes is not None:
            inicio, fim = parse_ano_mes(ano_mes)

        budgets = self.budget_repository.list_by_user_id(user_id, ativo=None)

        transacoes: List[TransacaoResult] = []
        for budget in budgets:
            if budget_id is not None and budget.id != budget_id:
                continue
            for lanc in budget.lancamentos:
                if tipo is not None and lanc.tipo.value != tipo:
                    continue
                if inicio is not None and not (inicio <= lanc.data < fim):
                    continue
                transacoes.append(
                    TransacaoResult(
                        id=lanc.id,
                        budget_id=budget.id,
                        budget_nome=budget.nome,
                        budget_categoria=budget.categoria,
                        descricao=lanc.descricao,
                        valor=float(lanc.valor.amount),
                        data=lanc.data,
                        categoria=lanc.categoria,
                        tipo=lanc.tipo.value,
                        conta=lanc.conta,
                        metodo_pagamento=lanc.metodo_pagamento.value,
                        pendente=lanc.pendente,
                    )
                )

        transacoes.sort(key=lambda t: t.data, reverse=True)

        total = len(transacoes)
        start = (page - 1) * page_size
        page_transacoes = transacoes[start : start + page_size]

        return page_transacoes, total