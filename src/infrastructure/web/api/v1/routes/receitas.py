"""
Routes for Receita (income) operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from src.infrastructure.web.api.v1.schemas.receita_schema import ReceitaCreate, ReceitaResponse
from src.application.budgeting.add_receita import AdicionarReceitaUseCase
from src.infrastructure.web.api.v1.dependencies import get_adicionar_receita_use_case
from src.infrastructure.web.api.v1.auth.jwt_auth import get_user_id_from_token_or_query

router = APIRouter(prefix="/receitas", tags=["receitas"])


@router.post(
    "/",
    response_model=ReceitaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona uma nova receita a um orçamento",
    description="Cria um novo lançamento do tipo ENTRADA (receita) no orçamento especificado.",
)
def adicionar_receita(
    payload: ReceitaCreate,
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    use_case: AdicionarReceitaUseCase = Depends(get_adicionar_receita_use_case),
):
    """
    Add income to a budget.
    
    This endpoint creates a new ENTRADA (income) transaction and adds it to the specified budget.
    The transaction includes all required fields: valor, data, descricao, categoria.
    """
    # Extract user_id from JWT token or query param
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)
    
    try:
        receita = use_case.execute(
            budget_id=payload.budget_id,
            valor=payload.valor,
            data=payload.data,
            descricao=payload.descricao,
            categoria=payload.categoria,
            user_id=effective_user_id,
            conta=payload.conta,
            metodo_pagamento=payload.metodo_pagamento,
            pendente=payload.pendente,
        )
    except ValueError as exc:
        # Domain validation errors become 400 Bad Request
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        # Unexpected errors -> 500 Internal Server Error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return ReceitaResponse(
        id=receita.id,
        budget_id=receita.budget_id,
        valor=float(receita.valor.amount),
        data=receita.data,
        descricao=receita.descricao,
        categoria=receita.categoria,
        tipo=receita.tipo.value,
        data_criacao=receita.data_criacao,
        conta=receita.conta,
        metodo_pagamento=receita.metodo_pagamento.value,
        pendente=receita.pendente,
    )
