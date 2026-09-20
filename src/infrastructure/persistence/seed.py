"""Dados de demonstração para a Yeldify API (desenvolvimento).

Popula o repositório com orçamentos e lançamentos de exemplo para um usuário,
espelhando o cenário que o front mockava. Usado tanto pelo script
`scripts/seed_demo.py` quanto pelo startup da API (env `SEED_DEMO=true`).
"""
from datetime import date
from decimal import Decimal

from src.domain.budgeting.budget import Budget
from src.domain.budgeting.lancamento import Lancamento, MetodoPagamento, TipoLancamento
from src.domain.budgeting.money import Money
from src.infrastructure.persistence.repositories import IBudgetRepository

DEFAULT_USER_ID = "user-123"


def _dias(hoje: date, dia: int) -> date:
    """Data no mês corrente (dias <= 28 para evitar problemas de fim de mês)."""
    return hoje.replace(day=dia)


def _lanc(idd: str, valor: float, dia: int, descricao: str, categoria: str,
          budget_id: str, tipo: TipoLancamento, hoje: date,
          conta: str = "Cartão Nubank • Crédito",
          metodo: MetodoPagamento = MetodoPagamento.CARTAO,
          pendente: bool = False) -> Lancamento:
    return Lancamento(
        id=idd,
        budget_id=budget_id,
        valor=Money(Decimal(str(valor)), "BRL"),
        data=_dias(hoje, dia),
        descricao=descricao,
        tipo=tipo,
        categoria=categoria,
        conta=conta,
        metodo_pagamento=metodo,
        pendente=pendente,
    )


def _make_budget(budget_id: str, nome: str, categoria: str, limite: float,
                 hoje: date, ativo: bool = True) -> Budget:
    return Budget(
        id=budget_id,
        user_id=DEFAULT_USER_ID,
        nome=nome,
        categoria=categoria,
        start_date=hoje.replace(day=1),
        end_date=hoje.replace(day=28),
        limite=Money(Decimal(str(limite)), "BRL"),
        _ativo=ativo,
        created_at=hoje.replace(day=1),
    )


def seed_demo(repo: IBudgetRepository, user_id: str = DEFAULT_USER_ID, force: bool = False) -> bool:
    """Aplica os seeds de demonstração.

    Returns:
        True se os seeds foram aplicados; False se já haviam dados e force=False.
    """
    if not force and repo.list_by_user_id(user_id, ativo=None):
        return False

    hoje = date.today()

    b_alim = _make_budget("b-alim", "iFood & Restaurantes", "Restaurante", 500.0, hoje)
    for args in [
        ("l-alim-1", 85.90, 17, "Ifood *Hamburgueria", "Restaurante"),
        ("l-alim-2", 215.00, 14, "Restaurante Centro", "Restaurante"),
        ("l-alim-3", 95.10, 10, "Ifood *Pizza", "Restaurante"),
        ("l-alim-4", 90.00, 6, "Lanchonete Express", "Restaurante"),
        ("l-alim-5", 100.00, 5, "Ifood *Almoço", "Restaurante"),
    ]:
        b_alim.adicionar_lancamento(_lanc(*args, b_alim.id, TipoLancamento.SAIDA, hoje))

    b_transp = _make_budget("b-transp", "Transporte", "Transporte", 400.0, hoje)
    for args in [
        ("l-transp-1", 28.50, 16, "Uber *Trip SP", "Transporte"),
        ("l-transp-2", 200.00, 14, "Combustível", "Transporte"),
        ("l-transp-3", 61.50, 8, "Uber *Daily", "Transporte"),
        ("l-transp-4", 50.00, 2, "Bilhete Único", "Transporte"),
    ]:
        b_transp.adicionar_lancamento(_lanc(*args, b_transp.id, TipoLancamento.SAIDA, hoje))

    b_super = _make_budget("b-super", "Supermercado", "Supermercado", 800.0, hoje)
    for args in [
        ("l-super-1", 240.00, 6, "Supermercado Pão de Açúcar", "Supermercado"),
        ("l-super-2", 100.00, 3, "Padaria Trigo Dourado", "Supermercado"),
    ]:
        b_super.adicionar_lancamento(_lanc(*args, b_super.id, TipoLancamento.SAIDA, hoje))

    b_assin = _make_budget("b-assin", "Assinaturas", "Assinaturas", 200.0, hoje)
    for args in [
        ("l-assin-1", 55.90, 1, "Netflix", "Assinaturas"),
        ("l-assin-2", 21.90, 1, "Spotify", "Assinaturas"),
        ("l-assin-3", 24.90, 1, "iCloud", "Assinaturas"),
    ]:
        b_assin.adicionar_lancamento(_lanc(*args, b_assin.id, TipoLancamento.SAIDA, hoje))
    b_assin.adicionar_lancamento(_lanc(
        "l-assin-4", 45.00, 15, "Loja Misteriosa *Online", "Outros",
        b_assin.id, TipoLancamento.SAIDA, hoje,
        conta="Carteira Física • Espécie",
        metodo=MetodoPagamento.ESPECIE, pendente=True,
    ))

    b_saude = _make_budget("b-saude", "Saúde & Academia", "Saúde", 300.0, hoje)
    for args in [
        ("l-saude-1", 150.00, 13, "Farmácia Popular", "Saúde"),
        ("l-saude-2", 120.00, 1, "Academia Bodytech", "Saúde"),
    ]:
        b_saude.adicionar_lancamento(_lanc(*args, b_saude.id, TipoLancamento.SAIDA, hoje))

    b_renda = _make_budget("b-renda", "Renda", "Renda", 9000.0, hoje)
    for args in [
        ("l-renda-1", 8500.00, 5, "Salário Mensal", "Renda"),
        ("l-renda-2", 1200.00, 12, "Pix: Cliente X", "Renda"),
    ]:
        b_renda.adicionar_lancamento(_lanc(*args, b_renda.id, TipoLancamento.ENTRADA, hoje,
                                           conta="Itaú • Conta Corrente", metodo=MetodoPagamento.PIX))

    b_viagem = _make_budget("b-viagem", "Viagem de Férias", "Lazer", 4000.0, hoje, ativo=False)
    b_viagem.lancamentos = [
        _lanc("l-viagem-1", 1200.00, 10, "Passagem Aérea", "Lazer",
              b_viagem.id, TipoLancamento.SAIDA, hoje, conta="Cartão XP • Crédito"),
        _lanc("l-viagem-2", 800.00, 11, "Hotel Reserva", "Lazer",
              b_viagem.id, TipoLancamento.SAIDA, hoje, conta="Cartão XP • Crédito"),
    ]

    for b in (b_alim, b_transp, b_super, b_assin, b_saude, b_renda, b_viagem):
        repo.save(b)

    return True