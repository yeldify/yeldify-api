from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from typing import Optional

from src.application.budgeting.dashboard_micro import DashboardMicroUseCase
from src.infrastructure.web.api.v1.dependencies import get_dashboard_micro_use_case
from src.infrastructure.web.api.v1.auth.jwt_auth import get_user_id_from_token_or_query
from src.infrastructure.web.api.v1.schemas.dashboard_schema import (
    DashboardMicroResponse,
    DesvioResponse,
    OrcamentoStatusResponse,
    ResumoMicroResponse,
)
from src.infrastructure.web.api.v1.schemas.transacao_schema import TransacaoResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/micro",
    response_model=DashboardMicroResponse,
    status_code=status.HTTP_200_OK,
    summary="Resumo do mês corrente para o painel micro",
)
def dashboard_micro(
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    ano_mes: Optional[str] = Query(None, description="Mês no formato YYYY-MM (padrão: mês corrente)"),
    use_case: DashboardMicroUseCase = Depends(get_dashboard_micro_use_case),
):
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)

    try:
        result = use_case.execute(user_id=effective_user_id, ano_mes=ano_mes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return DashboardMicroResponse(
        resumo=ResumoMicroResponse(
            saldo_disponivel=result.resumo.saldo_disponivel,
            total_receitas=result.resumo.total_receitas,
            total_despesas=result.resumo.total_despesas,
            qtd_orcamentos_ativos=result.resumo.qtd_orcamentos_ativos,
        ),
        orcamentos=[
            OrcamentoStatusResponse(
                id=o.id,
                nome=o.nome,
                categoria=o.categoria,
                teto=o.teto,
                gasto=o.gasto,
                percentual=o.percentual,
                status=o.status,
            )
            for o in result.orcamentos
        ],
        desvios=[
            DesvioResponse(
                budget_id=d.budget_id,
                nome=d.nome,
                percentual=d.percentual,
                excedente=d.excedente,
                dias_restantes=d.dias_restantes,
            )
            for d in result.desvios
        ],
        transacoes_recentes=[
            TransacaoResponse(
                id=t.id,
                budget_id=t.budget_id,
                budget_nome=t.budget_nome,
                budget_categoria=t.budget_categoria,
                descricao=t.descricao,
                valor=t.valor,
                data=t.data,
                categoria=t.categoria,
                tipo=t.tipo,
                conta=t.conta,
                metodo_pagamento=t.metodo_pagamento,
                pendente=t.pendente,
            )
            for t in result.transacoes_recentes
        ],
    )