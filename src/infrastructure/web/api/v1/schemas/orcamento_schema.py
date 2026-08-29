from pydantic import BaseModel
from datetime import date
from typing import Optional

class OrcamentoResponse(BaseModel):
    id: str
    nome: str
    categoria: str
    valor_restante: float
    valor_planejado: float
    data_criacao: date
    ativo: bool

    class Config:
        orm_mode = True