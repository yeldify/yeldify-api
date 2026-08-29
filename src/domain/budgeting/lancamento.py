from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from datetime import date
from src.domain.budgeting.money import Money


class TipoLancamento(Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


@dataclass(frozen=True)
class Lancamento:
    id: str
    budget_id: str
    valor: Money
    data: date
    descricao: str
    tipo: TipoLancamento

    def __post_init__(self):
        if not self.id or not isinstance(self.id, str):
            raise ValueError("id must be a non-empty string")
        if not self.budget_id or not isinstance(self.budget_id, str):
            raise ValueError("budget_id must be a non-empty string")
        if not isinstance(self.valor, Money):
            raise ValueError("valor must be a Money instance")
        if not isinstance(self.data, date):
            raise ValueError("data must be a date instance")
        if not self.descricao or not isinstance(self.descricao, str):
            raise ValueError("descricao must be a non-empty string")
        if not isinstance(self.tipo, TipoLancamento):
            raise ValueError("tipo must be a TipoLancamento")