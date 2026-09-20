from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from src.infrastructure.web.api.v1.schemas.despesa_schema import DespesaCreate, DespesaResponse
from src.application.budgeting.add_expense import AdicionarDespesaUseCase
from src.infrastructure.web.api.v1.dependencies import get_adicionar_despesa_use_case
from src.infrastructure.web.api.v1.auth.jwt_auth import get_user_id_from_token_or_query

router = APIRouter(prefix="/despesas", tags=["despesas"])

@router.post(
    "/",
    response_model=DespesaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona uma nova despesa a um orçamento",
)
def adicionar_despesa(
    payload: DespesaCreate,
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    use_case: AdicionarDespesaUseCase = Depends(get_adicionar_despesa_use_case),
):
    # Extract user_id from JWT token or query param
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)
    
    try:
        expense = use_case.execute(
            budget_id=payload.budget_id,
            valor=payload.valor,
            data=payload.data,
            descricao=payload.descricao,
            user_id=effective_user_id,
            categoria=payload.categoria,
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

    return DespesaResponse(
        id=expense.id,
        budget_id=expense.budget_id,
        valor=float(expense.valor.amount),
        data=expense.data,
        descricao=expense.descricao,
        categoria=expense.categoria,
        conta=expense.conta,
        metodo_pagamento=expense.metodo_pagamento.value,
        pendente=expense.pendente,
    )