from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.infrastructure.web.api.v1.schemas.orcamento_schema import OrcamentoResponse
from src.infrastructure.web.api.v1.schemas.orcamento_update_schema import OrcamentoUpdate
from src.application.budgeting.list_orcamentos import ListarOrcamentosUseCase
from src.application.budgeting.editar_orcamento import EditarOrcamentoUseCase
from src.infrastructure.web.api.v1.dependencies import get_listar_orcamentos_use_case, get_editar_orcamento_use_case

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])

@router.get(
    "/",
    response_model=list[OrcamentoResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista orçamentos ativos de um usuário com ordenação e paginação",
)
def listar_orcamentos(
    user_id: str = Query(..., description="ID do usuário logado (em produção viria do token JWT)"),
    sort_by: str = Query("nome", description="Campo para ordenação: nome, valor_restante, valor_planejado, data_criacao"),
    page: int = Query(1, ge=1, description="Número da página (começando em 1)"),
    page_size: int = Query(10, ge=1, description="Itens por página"),
    use_case: ListarOrcamentosUseCase = Depends(get_listar_orcamentos_use_case),
):
    try:
        budgets = use_case.execute(
            user_id=user_id,
            sort_by=sort_by,
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

    # Map Budget objects to response schema
    return [
        OrcamentoResponse(
            id=b.id,
            nome=b.nome,
            categoria=b.categoria,
            valor_restante=float(b.saldo.amount),
            valor_planejado=float(b.limite.amount),
            data_criacao=b.created_at,
        )
        for b in budgets
    ]


@router.put(
    "/{budget_id}",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_200_OK,
    summary="Edita um orçamento existente",
)
def editar_orcamento(
    budget_id: str,
    payload: OrcamentoUpdate,
    user_id: str = Query(..., description="ID do usuário logado (em produção viria do token JWT)"),
    use_case: EditarOrcamentoUseCase = Depends(get_editar_orcamento_use_case),
):
    try:
        budget = use_case.execute(
            budget_id=budget_id,
            user_id=user_id,
            nome=payload.nome,
            valor=payload.valor,
            validade_meses=payload.validade_meses,
            ativo=payload.ativo,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return OrcamentoResponse(
        id=budget.id,
        nome=budget.nome,
        categoria=budget.categoria,
        valor_restante=float(budget.saldo.amount),
        valor_planejado=float(budget.limite.amount),
        data_criacao=budget.created_at,
    )