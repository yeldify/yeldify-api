from fastapi import APIRouter, Depends, HTTPException, status
from src.infrastructure.web.api.v1.schemas.despesa_schema import DespesaCreate, DespesaResponse
from src.application.budgeting.add_expense import AdicionarDespesaUseCase
from src.infrastructure.web.api.v1.dependencies import get_adicionar_despesa_use_case
from src.domain.budgeting.money import Money

router = APIRouter(prefix="/despesas", tags=["despesas"])

@router.post(
    "/",
    response_model=DespesaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona uma nova despesa a um orçamento",
)
def adicionar_despesa(
    payload: DespesaCreate,
    use_case: AdicionarDespesaUseCase = Depends(get_adicionar_despesa_use_case),
):
    try:
        expense = use_case.execute(
            budget_id=payload.budget_id,
            valor=Money(payload.valor, "BRL"),  # assume BRL for now
            data=payload.data,
            descricao=payload.descricao,
            user_id="user-fake",  # In a real app this comes from auth (JWT, session, etc.)
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
    )