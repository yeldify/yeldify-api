from pydantic import BaseModel, field_validator
from typing import Optional


class OrcamentoUpdate(BaseModel):
    nome: Optional[str] = None
    valor: Optional[float] = None
    validade_meses: Optional[int] = None
    ativo: Optional[bool] = None
    nota_governanca: Optional[str] = None

    @field_validator("nota_governanca")
    @classmethod
    def gouvernanca_nao_vazia(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Justificativa não pode ser vazia ou apenas espaços")
        return v.strip() if v is not None else v

    class Config:
        orm_mode = True