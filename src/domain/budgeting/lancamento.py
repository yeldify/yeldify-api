from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from datetime import date
from src.domain.budgeting.money import Money


class TipoLancamento(Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class MetodoPagamento(Enum):
    CARTAO = "cartao"
    ESPECIE = "especie"
    PIX = "pix"
    OUTROS = "outros"


@dataclass(frozen=True)
class Lancamento:
    id: str
    budget_id: str
    valor: Money
    data: date
    descricao: str
    tipo: TipoLancamento
    categoria: str = "Outros"
    conta: str = "Não informada"
    metodo_pagamento: MetodoPagamento = MetodoPagamento.OUTROS
    pendente: bool = False
    data_criacao: date = field(default_factory=date.today)

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
        if not self.categoria or not isinstance(self.categoria, str):
            raise ValueError("categoria must be a non-empty string")
        if not self.conta or not isinstance(self.conta, str):
            raise ValueError("conta must be a non-empty string")
        if not isinstance(self.metodo_pagamento, MetodoPagamento):
            raise ValueError("metodo_pagamento must be a MetodoPagamento")
        if not isinstance(self.pendente, bool):
            raise ValueError("pendente must be a bool")
        if not isinstance(self.data_criacao, date):
            raise ValueError("data_criacao must be a date instance")