from pydantic import BaseModel
from datetime import date
from typing import List


class TransacaoResponse(BaseModel):
    id: str
    budget_id: str
    budget_nome: str
    budget_categoria: str
    descricao: str
    valor: float
    data: date
    categoria: str
    tipo: str  # ENTRADA or SAIDA
    conta: str
    metodo_pagamento: str  # cartao | especie | pix | outros
    pendente: bool

    class Config:
        orm_mode = True


class TransacaoListResponse(BaseModel):
    items: List[TransacaoResponse]
    total: int
    page: int
    page_size: int

    class Config:
        orm_mode = True