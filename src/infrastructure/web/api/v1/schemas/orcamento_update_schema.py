from pydantic import BaseModel
from typing import Optional

class OrcamentoUpdate(BaseModel):
    nome: Optional[str] = None
    valor: Optional[float] = None
    validade_meses: Optional[int] = None
    ativo: Optional[bool] = None

    class Config:
        orm_mode = True