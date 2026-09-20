from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Optional, Tuple

from src.application.budgeting.listar_transacoes import TransacaoResult
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.lancamento import Lancamento, MetodoPagamento
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository


class EditarTransacaoUseCase:
    """Atualiza campos opcionais de um lançamento existente do usuário."""

    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    def execute(
        self,
        lancamento_id: str,
        user_id: str,
        *,
        descricao: Optional[str] = None,
        categoria: Optional[str] = None,
        conta: Optional[str] = None,
        metodo_pagamento: Optional[MetodoPagamento] = None,
        pendente: Optional[bool] = None,
        valor: Optional[float] = None,
        data: Optional[date] = None,
    ) -> TransacaoResult:
        if not lancamento_id or not isinstance(lancamento_id, str):
            raise ValueError("lancamento_id must be a non-empty string")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")

        budget, lancamento = self._find_lancamento(lancamento_id, user_id)
        if budget is None or lancamento is None:
            raise ValueError(f"Lancamento with id {lancamento_id} not found")

        updates = self._build_updates(
            descricao=descricao,
            categoria=categoria,
            conta=conta,
            metodo_pagamento=metodo_pagamento,
            pendente=pendente,
            valor=valor,
            data=data,
        )
        if not updates:
            raise ValueError("No fields provided for update")

        novo_lancamento = replace(lancamento, **updates)
        budget.lancamentos = [
            novo_lancamento if l.id == lancamento_id else l for l in budget.lancamentos
        ]
        self.budget_repository.save(budget)

        return TransacaoResult(
            id=novo_lancamento.id,
            budget_id=budget.id,
            budget_nome=budget.nome,
            budget_categoria=budget.categoria,
            descricao=novo_lancamento.descricao,
            valor=float(novo_lancamento.valor.amount),
            data=novo_lancamento.data,
            categoria=novo_lancamento.categoria,
            tipo=novo_lancamento.tipo.value,
            conta=novo_lancamento.conta,
            metodo_pagamento=novo_lancamento.metodo_pagamento.value,
            pendente=novo_lancamento.pendente,
        )

    @staticmethod
    def _build_updates(
        *,
        descricao: Optional[str],
        categoria: Optional[str],
        conta: Optional[str],
        metodo_pagamento: Optional[MetodoPagamento],
        pendente: Optional[bool],
        valor: Optional[float],
        data: Optional[date],
    ) -> dict:
        updates: dict = {}

        if descricao is not None:
            descricao = descricao.strip()
            if not descricao:
                raise ValueError("descricao cannot be empty")
            updates["descricao"] = descricao

        if categoria is not None:
            categoria = categoria.strip()
            if not categoria:
                raise ValueError("categoria cannot be empty")
            updates["categoria"] = categoria

        if conta is not None:
            conta = conta.strip()
            if not conta:
                raise ValueError("conta cannot be empty")
            updates["conta"] = conta

        if metodo_pagamento is not None:
            if isinstance(metodo_pagamento, str):
                try:
                    metodo_pagamento = MetodoPagamento(metodo_pagamento)
                except ValueError:
                    raise ValueError(
                        "metodo_pagamento must be one of cartao, especie, pix, outros"
                    )
            updates["metodo_pagamento"] = metodo_pagamento

        if pendente is not None:
            if not isinstance(pendente, bool):
                raise ValueError("pendente must be a boolean")
            updates["pendente"] = pendente

        if valor is not None:
            if valor <= 0:
                raise ValueError("valor must be greater than zero")
            updates["valor"] = Money(valor, "BRL")

        if data is not None:
            if not isinstance(data, date):
                raise ValueError("data must be a date")
            updates["data"] = data

        return updates

    def _find_lancamento(
        self, lancamento_id: str, user_id: str
    ) -> Tuple[Optional[Budget], Optional[Lancamento]]:
        budgets = self.budget_repository.list_by_user_id(user_id, ativo=None)
        for budget in budgets:
            for lancamento in budget.lancamentos:
                if lancamento.id == lancamento_id:
                    return budget, lancamento
        return None, None