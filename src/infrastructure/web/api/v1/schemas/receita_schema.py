"""
Schemas for Receita (income) API.
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from src.domain.budgeting.lancamento import MetodoPagamento


class ReceitaCreate(BaseModel):
    """Schema for creating a new income/revenue."""
    budget_id: str = Field(..., example="budget-123", description="ID do orçamento")
    valor: float = Field(..., gt=0, example=2500.0, description="Valor da receita (deve ser positivo)")
    data: date = Field(..., example="2026-08-27", description="Data de recebimento")
    descricao: str = Field(..., min_length=1, example="Salário", description="Descrição da receita")
    categoria: str = Field(..., min_length=1, example="Salário", description="Categoria da receita")
    conta: str = Field("Não informada", example="Itaú • Conta Corrente", description="Conta/Serviço")
    metodo_pagamento: MetodoPagamento = Field(MetodoPagamento.OUTROS, example="pix")
    pendente: bool = False

    class Config:
        orm_mode = True


class ReceitaResponse(BaseModel):
    """Schema for income/revenue response."""
    id: str
    budget_id: str
    valor: float
    data: date
    descricao: str
    categoria: str
    tipo: str  # ENTRADA or SAIDA
    data_criacao: date
    conta: str
    metodo_pagamento: str
    pendente: bool

    class Config:
        orm_mode = True
