import pytest
from datetime import date
from decimal import Decimal

from src.application.budgeting.editar_transacao import EditarTransacaoUseCase
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.lancamento import Lancamento, MetodoPagamento, TipoLancamento
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository


def make_lanc(id_lanc: str, valor: float, descricao: str, categoria: str,
              tipo: TipoLancamento = TipoLancamento.SAIDA, pendente: bool = False) -> Lancamento:
    return Lancamento(
        id=id_lanc,
        budget_id="b1",
        valor=Money(valor, "BRL"),
        data=date(2026, 9, 10),
        descricao=descricao,
        tipo=tipo,
        categoria=categoria,
        conta="Cartão Nubank • Crédito",
        metodo_pagamento=MetodoPagamento.CARTAO,
        pendente=pendente,
    )


def make_repo(lancamentos=None):
    repo = InMemoryBudgetRepository()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Alimentação",
        categoria="Essencial",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(1500.0, "BRL"),
    )
    for l in lancamentos or [make_lanc("l1", 85.90, "Ifood", "Restaurante")]:
        budget.adicionar_lancamento(l)
    repo.save(budget)
    return repo


def test_editar_transacao_categoria():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    result = use_case.execute(
        lancamento_id="l1",
        user_id="user-123",
        categoria="Alimentação",
    )
    assert result.categoria == "Alimentação"
    assert result.pendente is False
    assert result.conta == "Cartão Nubank • Crédito"
    # persisted
    budget = repo.get("b1")
    assert budget.lancamentos[0].categoria == "Alimentação"


def test_editar_transacao_conta_metodo_pendente():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    result = use_case.execute(
        lancamento_id="l1",
        user_id="user-123",
        conta="Carteira Física • Espécie",
        metodo_pagamento=MetodoPagamento.ESPECIE,
        pendente=True,
    )
    assert result.conta == "Carteira Física • Espécie"
    assert result.metodo_pagamento == "especie"
    assert result.pendente is True


def test_editar_transacao_metodo_pagamento_str():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    result = use_case.execute(
        lancamento_id="l1",
        user_id="user-123",
        metodo_pagamento="pix",
    )
    assert result.metodo_pagamento == "pix"


def test_editar_transacao_metodo_pagamento_invalido():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="metodo_pagamento"):
        use_case.execute(lancamento_id="l1", user_id="user-123", metodo_pagamento="bitcoin")


def test_editar_transacao_categoria_vazia_erro():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="categoria cannot be empty"):
        use_case.execute(lancamento_id="l1", user_id="user-123", categoria="   ")


def test_editar_transacao_nenhum_campo_erro():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="No fields provided"):
        use_case.execute(lancamento_id="l1", user_id="user-123")


def test_editar_transacao_lancamento_inexistente():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="not found"):
        use_case.execute(lancamento_id="l-404", user_id="user-123", categoria="X")


def test_editar_transacao_outro_usuario_nao_encontra():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="not found"):
        use_case.execute(lancamento_id="l1", user_id="user-456", categoria="X")


# ==================== REALOCAÇÃO ENTRE ORÇAMENTOS ====================

def make_repo_dois_orcamentos():
    repo = make_repo()
    b2 = Budget(
        id="b2",
        user_id="user-123",
        nome="Transporte",
        categoria="Essencial",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(500.0, "BRL"),
    )
    repo.save(b2)
    return repo


def test_realocar_transacao_para_outro_orcamento_success():
    repo = make_repo_dois_orcamentos()
    use_case = EditarTransacaoUseCase(repo)
    result = use_case.execute(
        lancamento_id="l1",
        user_id="user-123",
        budget_id="b2",
    )
    assert result.budget_id == "b2"
    assert result.budget_nome == "Transporte"
    # campos da transação preservados
    assert result.descricao == "Ifood"
    assert result.valor == 85.90
    assert result.categoria == "Restaurante"
    # persistência: origem sem a transação, destino com ela
    assert repo.get("b1").lancamentos == []
    assert [l.id for l in repo.get("b2").lancamentos] == ["l1"]


def test_realocar_transacao_com_edicao_combinada():
    repo = make_repo_dois_orcamentos()
    use_case = EditarTransacaoUseCase(repo)
    result = use_case.execute(
        lancamento_id="l1",
        user_id="user-123",
        budget_id="b2",
        categoria="Transporte",
    )
    assert result.budget_id == "b2"
    assert result.categoria == "Transporte"
    movida = repo.get("b2").lancamentos[0]
    assert movida.categoria == "Transporte"


def test_realocar_transacao_destino_inexistente():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="Orçamento de destino não encontrado"):
        use_case.execute(lancamento_id="l1", user_id="user-123", budget_id="b-404")
    assert [l.id for l in repo.get("b1").lancamentos] == ["l1"]


def test_realocar_transacao_destino_outro_usuario():
    repo = make_repo()
    b_outro = Budget(
        id="b9",
        user_id="user-456",
        nome="Outro Usuário",
        categoria="Essencial",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(500.0, "BRL"),
    )
    repo.save(b_outro)
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="orçamento de outro usuário"):
        use_case.execute(lancamento_id="l1", user_id="user-123", budget_id="b9")
    assert [l.id for l in repo.get("b1").lancamentos] == ["l1"]


def test_realocar_transacao_destino_inativo():
    repo = make_repo()
    b_arq = Budget(
        id="b-arq",
        user_id="user-123",
        nome="Arquivado",
        categoria="Lazer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        limite=Money(500.0, "BRL"),
        _ativo=False,
    )
    repo.save(b_arq)
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="orçamento inativo"):
        use_case.execute(lancamento_id="l1", user_id="user-123", budget_id="b-arq")
    assert [l.id for l in repo.get("b1").lancamentos] == ["l1"]


def test_realocar_transacao_mesmo_orcamento_sem_campos_erro():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    with pytest.raises(ValueError, match="No fields provided"):
        use_case.execute(lancamento_id="l1", user_id="user-123", budget_id="b1")


def test_realocar_transacao_mesmo_orcamento_edita_normalmente():
    repo = make_repo()
    use_case = EditarTransacaoUseCase(repo)
    result = use_case.execute(
        lancamento_id="l1",
        user_id="user-123",
        budget_id="b1",
        categoria="Alimentação",
    )
    assert result.budget_id == "b1"
    assert result.categoria == "Alimentação"