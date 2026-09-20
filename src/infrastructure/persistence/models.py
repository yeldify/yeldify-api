"""
SQLAlchemy models for Budget and Lancamento entities.
Maps domain objects to PostgreSQL tables.
"""
from sqlalchemy import Column, String, Date, Boolean, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import date
from src.infrastructure.persistence.database import Base
from src.domain.budgeting.lancamento import TipoLancamento, MetodoPagamento


class BudgetModel(Base):
    """
    SQLAlchemy model for Budget aggregate.
    Maps to 'budgets' table.
    """
    __tablename__ = "budgets"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    limite_amount = Column(Numeric(12, 2), nullable=False)  # Decimal(12,2) for money
    limite_currency = Column(String(3), nullable=False, default="BRL")
    _ativo = Column(Boolean, nullable=False, default=True)
    created_at = Column(Date, nullable=False)
    nota_governanca = Column(String, nullable=True)
    
    # Relationship to LancamentoModel
    lancamentos = relationship("LancamentoModel", back_populates="budget", cascade="all, delete-orphan")


class LancamentoModel(Base):
    """
    SQLAlchemy model for Lancamento entity.
    Maps to 'lancamentos' table.
    """
    __tablename__ = "lancamentos"
    
    id = Column(String, primary_key=True, index=True)
    budget_id = Column(String, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True)
    valor_amount = Column(Numeric(12, 2), nullable=False)
    valor_currency = Column(String(3), nullable=False, default="BRL")
    data = Column(Date, nullable=False)
    descricao = Column(String, nullable=False)
    tipo = Column(Enum(TipoLancamento), nullable=False)
    categoria = Column(String, nullable=False, default="Outros")
    conta = Column(String, nullable=False, default="Não informada")
    metodo_pagamento = Column(Enum(MetodoPagamento), nullable=False, default=MetodoPagamento.OUTROS)
    pendente = Column(Boolean, nullable=False, default=False)
    data_criacao = Column(Date, nullable=False, default=date.today)
    
    # Relationship to BudgetModel
    budget = relationship("BudgetModel", back_populates="lancamentos")
