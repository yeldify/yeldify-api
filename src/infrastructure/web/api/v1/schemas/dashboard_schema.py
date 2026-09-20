from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from src.infrastructure.web.api.v1.schemas.transacao_schema import TransacaoResponse


class ResumoMicroResponse(BaseModel):
    saldo_disponivel: float
    total_receitas: float
    total_despesas: float
    qtd_orcamentos_ativos: int


class OrcamentoStatusResponse(BaseModel):
    id: str
    nome: str
    categoria: str
    teto: float
    gasto: float
    percentual: float
    status: str  # ok | atencao | estourado


class DesvioResponse(BaseModel):
    budget_id: str
    nome: str
    percentual: float
    excedente: float
    dias_restantes: int


class DashboardMicroResponse(BaseModel):
    resumo: ResumoMicroResponse
    orcamentos: List[OrcamentoStatusResponse]
    desvios: List[DesvioResponse]
    transacoes_recentes: List[TransacaoResponse]

    class Config:
        orm_mode = True