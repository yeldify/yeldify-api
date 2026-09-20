import pytest
from datetime import date, timedelta
from decimal import Decimal
from src.application.budgeting.editar_orcamento import EditarOrcamentoUseCase
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento


def test_editar_orcamento_success_nome():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Antigo Nome",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        nome="Novo Nome",
    )
    assert updated.nome == "Novo Nome"
    # other fields unchanged
    assert updated.categoria == "Essencial"
    assert updated.limite.amount == Decimal('1000.0')
    assert updated.end_date == hoje + timedelta(days=30)
    assert updated.ativo is True


def test_editar_orcamento_success_valor():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        valor=750.0,
    )
    assert updated.limite.amount == Decimal('750.0')
    assert updated.nome == "Orçamento"


def test_editar_orcamento_success_valor_negativo_limite():
    # According to AC02, cannot set valor < 0. But AC03 says saldo pode ser negativo after transactions.
    # The limite (valor planejado) cannot be negative.
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(100.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Valor do orçamento não pode ser menor que zero"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            valor=-10.0,
        )


def test_editar_orcamento_success_validade():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje - timedelta(days=30),  # started a month ago
        end_date=hoje + timedelta(days=30),   # original 2 months from start? but we'll just set
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje - timedelta(days=30),
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    # edit validade to 1 month
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        validade_meses=1,
    )
    expected_end = hoje + timedelta(days=30)
    assert updated.end_date == expected_end
    # start_date unchanged
    assert updated.start_date == hoje - timedelta(days=30)


def test_editar_orcamento_success_ativar_desativar():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    # start with inactive budget
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=False,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    # activate
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        ativo=True,
    )
    assert updated.ativo is True
    # deactivate (should succeed if no transactions)
    updated2 = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        ativo=False,
    )
    assert updated2.ativo is False


def test_editar_orcamento_duplicate_name_error():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    b1 = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento Um",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    b2 = Budget(
        id="b2",
        user_id="user-123",
        nome="Orçamento Dois",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(2000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(b1)
    repo.save(b2)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Já existe um orçamento com este nome"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            nome="Orçamento Dois",  # trying to rename to b2's name
        )


def test_editar_orcamento_nome_vazio_error():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Campo vazio. Informe nome"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            nome="",
        )
    with pytest.raises(ValueError, match="Campo vazio. Informe nome"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            nome="   ",
        )


def test_editar_orcamento_validade_fora_permittedos_error():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Validade deve ser um dos valores: 1, 2, 3, 6, 9 ou 12 meses."):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            validade_meses=5,
        )
    with pytest.raises(ValueError, match="Validade deve ser um dos valores: 1, 2, 3, 6, 9 ou 12 meses."):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            validade_meses=18,
        )


def test_editar_orcamento_validade_expirado_error():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    # budget expired yesterday
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento Expirado",
        categoria="Essencial",
        start_date=hoje - timedelta(days=60),
        end_date=hoje - timedelta(days=1),  # yesterday
        limite=Money(500.0, "BRL"),
        _ativo=True,  # still active but expired
        created_at=hoje - timedelta(days=60),
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Não é possível editar a validade de um orçamento expirado."):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            validade_meses=1,
        )


def test_editar_orcamento_validade_expirado_can_still_edit_other_fields():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento Expirado",
        categoria="Essencial",
        start_date=hoje - timedelta(days=60),
        end_date=hoje - timedelta(days=1),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje - timedelta(days=60),
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    # can still change nome
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        nome="Novo Nome",
    )
    assert updated.nome == "Novo Nome"
    # can change valor
    updated2 = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        valor=300.0,
    )
    assert updated2.limite.amount == Decimal('300.0')
    # can activate/inactivate
    updated3 = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        ativo=False,
    )
    assert updated3.ativo is False


def test_editar_orcamento_desativar_com_transacoes_error():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento com Transacoes",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    # add a lancamento (saida)
    lanc = Lancamento(
        id="l1",
        budget_id=budget.id,
        valor=Money(200.0, "BRL"),
        data=hoje,
        descricao="Saida",
        tipo=TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Cannot deactivate budget while it has transactions"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            ativo=False,
        )


def test_editar_orcamento_desativar_sem_transacoes_success():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento sem Transacoes",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        ativo=False,
    )
    assert updated.ativo is False


def test_editar_orcamento_nao_altera_categoria():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(1000.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    # try to change categoria? there's no parameter for categoria in our use case, so it's not possible.
    # but we can ensure that after any edit, categoria remains same.
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        nome="Novo Nome",
        valor=2000.0,
        validade_meses=6,
    )
    assert updated.categoria == "Essencial"


def test_editar_orcamento_saldo_pode_ser_negativo_apos_transacoes():
    # AC03: Após edição o saldo do orçamento pode ser negativo (caso as transações somem mais que o valor planejado)
    # We test that after editing limite (valor) to a lower value, saldo can be negative if transactions exceed.
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    # add a saida greater than limite
    lanc = Lancamento(
        id="l1",
        budget_id=budget.id,
        valor=Money(600.0, "BRL"),
        data=hoje,
        descricao="Grande saída",
        tipo=TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    # edit limite to 400 (lower than the 600 saída)
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        valor=400.0,
        nota_governanca="Ajuste de teto com movimentações existentes",
    )
    # saldo = limite + (entradas - saidas) = 400 + (0 - 600) = -200
    assert updated.saldo.amount == Decimal('-200.0')
    assert updated.nota_governanca == "Ajuste de teto com movimentações existentes"


def test_editar_orcamento_nao_permite_editar_validade_se_expirado_ja_testado():
    # already covered in test_editar_orcamento_validade_expirado_error
    pass


def test_editar_orcamento_alterar_valor_com_transacoes_exige_justificativa():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    lanc = Lancamento(
        id="l1",
        budget_id=budget.id,
        valor=Money(200.0, "BRL"),
        data=hoje,
        descricao="Saida",
        tipo=TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Justificativa obrigatória para alterar orçamento com movimentações"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            valor=400.0,
        )


def test_editar_orcamento_alterar_valor_com_transacoes_e_justificativa_success():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    lanc = Lancamento(
        id="l1",
        budget_id=budget.id,
        valor=Money(200.0, "BRL"),
        data=hoje,
        descricao="Saida",
        tipo=TipoLancamento.SAIDA,
    )
    budget.adicionar_lancamento(lanc)
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        valor=400.0,
        nota_governanca="  Redução de teto após revisão mensal  ",
    )
    assert updated.limite.amount == Decimal('400.0')
    assert updated.nota_governanca == "Redução de teto após revisão mensal"


def test_editar_orcamento_alterar_valor_sem_transacoes_nao_exige_justificativa():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    updated = use_case.execute(
        budget_id="b1",
        user_id="user-123",
        valor=400.0,
    )
    assert updated.limite.amount == Decimal('400.0')
    assert updated.nota_governanca is None


def test_editar_orcamento_justificativa_vazia_error():
    repo = InMemoryBudgetRepository()
    hoje = date.today()
    budget = Budget(
        id="b1",
        user_id="user-123",
        nome="Orçamento",
        categoria="Essencial",
        start_date=hoje,
        end_date=hoje + timedelta(days=30),
        limite=Money(500.0, "BRL"),
        _ativo=True,
        created_at=hoje,
    )
    repo.save(budget)
    use_case = EditarOrcamentoUseCase(repo)
    with pytest.raises(ValueError, match="Justificativa não pode ser vazia"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            valor=400.0,
            nota_governanca="   ",
        )
    with pytest.raises(ValueError, match="Justificativa não pode ser vazia"):
        use_case.execute(
            budget_id="b1",
            user_id="user-123",
            nome="Novo Nome",
            nota_governanca="   ",
        )


def test_editar_orcamento_campos_obrigatorios_vazio_error():
    # already covered in test_editar_orcamento_nome_vazio_error
    # also test for valor and validade? they are optional in the sense that you can choose not to provide them.
    # but if provided, they must be valid.
    # we already test valor negative and validade invalid.
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])