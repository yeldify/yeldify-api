from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from typing import Optional

from src.application.budgeting.listar_transacoes import ListarTransacoesUseCase
from src.application.budgeting.editar_transacao import EditarTransacaoUseCase
from src.infrastructure.web.api.v1.dependencies import (
    get_listar_transacoes_use_case,
    get_editar_transacao_use_case,
)
from src.infrastructure.web.api.v1.auth.jwt_auth import get_user_id_from_token_or_query
from src.infrastructure.web.api.v1.schemas.transacao_schema import TransacaoResponse, TransacaoListResponse
from src.infrastructure.web.api.v1.schemas.transacao_update_schema import TransacaoUpdate

router = APIRouter(prefix="/transacoes", tags=["transacoes"])


def _to_response(t) -> TransacaoResponse:
    return TransacaoResponse(
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


@router.get(
    "/",
    response_model=TransacaoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lista transações do usuário com filtros e paginação",
)
def listar_transacoes(
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    tipo: Optional[str] = Query(None, description="Filtro por tipo: ENTRADA ou SAIDA"),
    ano_mes: Optional[str] = Query(None, description="Filtro por mês no formato YYYY-MM"),
    budget_id: Optional[str] = Query(None, description="Filtra por orçamento específico"),
    page: int = Query(1, ge=1, description="Número da página (começando em 1)"),
    page_size: int = Query(20, ge=1, description="Itens por página"),
    use_case: ListarTransacoesUseCase = Depends(get_listar_transacoes_use_case),
):
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)

    try:
        items, total = use_case.execute(
            user_id=effective_user_id,
            tipo=tipo,
            ano_mes=ano_mes,
            budget_id=budget_id,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return TransacaoListResponse(
        items=[_to_response(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{lancamento_id}",
    response_model=TransacaoResponse,
    status_code=status.HTTP_200_OK,
    summary="Edita campos de um lançamento",
    description="Atualiza campos opcionais (categoria, conta, método de pagamento, pendente, descrição, valor ou data) de um lançamento existente.",
)
def editar_transacao(
    lancamento_id: str,
    payload: TransacaoUpdate,
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    use_case: EditarTransacaoUseCase = Depends(get_editar_transacao_use_case),
):
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)

    try:
        result = use_case.execute(
            lancamento_id=lancamento_id,
            user_id=effective_user_id,
            descricao=payload.descricao,
            categoria=payload.categoria,
            conta=payload.conta,
            metodo_pagamento=payload.metodo_pagamento,
            pendente=payload.pendente,
            valor=payload.valor,
            data=payload.data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return _to_response(result)