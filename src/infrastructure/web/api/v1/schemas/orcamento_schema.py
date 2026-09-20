from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class OrcamentoResponse(BaseModel):
    id: str
    nome: str
    categoria: str
    valor_restante: float
    valor_planejado: float
    gasto: float
    data_criacao: date
    ativo: bool
    nota_governanca: Optional[str] = None

    class Config:
        orm_mode = True


class OrcamentoListResponse(BaseModel):
    items: List[OrcamentoResponse]
    total: int
    page: int
    page_size: int

    class Config:
        orm_mode = True