from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional
from src.domain.budgeting.lancamento import MetodoPagamento

class DespesaCreate(BaseModel):
    budget_id: str = Field(..., example="budget-123")
    valor: float = Field(..., example=25.50)
    data: date = Field(..., example="2026-08-27")
    descricao: str = Field(..., min_length=1, example="Supermercado")
    categoria: str = Field("Outros", example="Alimentação")
    conta: str = Field("Não informada", example="Cartão Nubank • Crédito")
    metodo_pagamento: MetodoPagamento = Field(MetodoPagamento.OUTROS, example="cartao")
    pendente: bool = False

    @validator("descricao")
    def descricao_nao_vazia(cls, v):
        if not v or not v.strip():
            raise ValueError("descrição cannot be empty or only whitespace")
        return v.strip()

    @validator("categoria")
    def categoria_nao_vazia(cls, v):
        if not v or not v.strip():
            raise ValueError("categoria cannot be empty or only whitespace")
        return v.strip()

    @validator("conta")
    def conta_nao_vazia(cls, v):
        if not v or not v.strip():
            raise ValueError("conta cannot be empty or only whitespace")
        return v.strip()

class DespesaResponse(BaseModel):
    id: str
    budget_id: str
    valor: float
    data: date
    descricao: str
    categoria: str
    conta: str
    metodo_pagamento: str
    pendente: bool