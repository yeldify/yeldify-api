from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import Optional

from src.domain.budgeting.lancamento import MetodoPagamento


class TransacaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    descricao: Optional[str] = None
    categoria: Optional[str] = None
    conta: Optional[str] = None
    metodo_pagamento: Optional[MetodoPagamento] = None
    pendente: Optional[bool] = None
    valor: Optional[float] = None
    data: Optional[date] = None
    budget_id: Optional[str] = None

    @field_validator("descricao", "categoria", "conta")
    @classmethod
    def campo_nao_vazio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("campo não pode ser vazio ou apenas espaços")
        return v.strip() if v is not None else v

    @field_validator("budget_id")
    @classmethod
    def budget_id_nao_vazio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("budget_id não pode ser vazio ou apenas espaços")
        return v.strip() if v is not None else v

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("valor deve ser maior que zero")
        return v