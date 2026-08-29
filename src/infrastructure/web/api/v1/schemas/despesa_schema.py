from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional

class DespesaCreate(BaseModel):
    budget_id: str = Field(..., example="budget-123")
    valor: float = Field(..., gt=0, example=25.50)
    data: date = Field(..., example="2026-08-27")
    descricao: str = Field(..., min_length=1, example="Supermercado")

    @validator("descricao")
    def descricao_nao_vazia(cls, v):
        if not v or not v.strip():
            raise ValueError("descrição cannot be empty or only whitespace")
        return v.strip()

class DespesaResponse(BaseModel):
    id: str
    budget_id: str
    valor: float
    data: date
    descricao: str