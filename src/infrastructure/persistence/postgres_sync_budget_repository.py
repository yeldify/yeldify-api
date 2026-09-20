"""
Synchronous PostgreSQL implementation of IBudgetRepository.
Uses SQLAlchemy with psycopg2 for sync operations.
Compatible with existing synchronous use cases.
"""
from typing import List, Optional
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker, Session
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.lancamento import Lancamento, TipoLancamento, MetodoPagamento
from src.infrastructure.persistence.repositories import IBudgetRepository
from src.infrastructure.persistence.models import BudgetModel, LancamentoModel
import os


class PostgresSyncBudgetRepository(IBudgetRepository):
    """
    Synchronous PostgreSQL-based repository for Budget aggregates.
    Uses SQLAlchemy with psycopg2 (sync driver).
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the repository with a database connection string.
        
        Args:
            connection_string: PostgreSQL connection string.
                Default: from DATABASE_URL environment variable.
        """
        db_url = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/yeldify"
        )
        
        # Replace asyncpg with psycopg2 for sync
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        self._engine = create_engine(db_url, echo=False)
        self._Session = sessionmaker(bind=self._engine)
    
    def _create_session(self) -> Session:
        """Create a new database session."""
        return self._Session()
    
    @staticmethod
    def _budget_to_model(budget: Budget) -> BudgetModel:
        """Convert Budget domain entity to BudgetModel."""
        return BudgetModel(
            id=budget.id,
            user_id=budget.user_id,
            nome=budget.nome,
            categoria=budget.categoria,
            start_date=budget.start_date,
            end_date=budget.end_date,
            limite_amount=float(budget.limite.amount),
            limite_currency=budget.limite.currency,
            _ativo=budget._ativo,
            created_at=budget.created_at,
            lancamentos=[
                LancamentoModel(
                    id=l.id,
                    budget_id=l.budget_id,
                    valor_amount=float(l.valor.amount),
                    valor_currency=l.valor.currency,
                    data=l.data,
                    descricao=l.descricao,
                    tipo=l.tipo,
                    categoria=l.categoria,
                    conta=l.conta,
                    metodo_pagamento=l.metodo_pagamento,
                    pendente=l.pendente,
                    data_criacao=l.data_criacao,
                )
                for l in budget.lancamentos
            ]
        )
    
    @staticmethod
    def _model_to_budget(model: BudgetModel) -> Budget:
        """Convert BudgetModel to Budget domain entity."""
        limite = Money(float(model.limite_amount), model.limite_currency)
        
        lancamentos = [
            Lancamento(
                id=lm.id,
                budget_id=lm.budget_id,
                valor=Money(float(lm.valor_amount), lm.valor_currency),
                data=lm.data,
                descricao=lm.descricao,
                tipo=lm.tipo,
                categoria=lm.categoria,
                conta=lm.conta,
                metodo_pagamento=lm.metodo_pagamento,
                pendente=lm.pendente,
                data_criacao=lm.data_criacao,
            )
            for lm in model.lancamentos
        ]
        
        return Budget(
            id=model.id,
            user_id=model.user_id,
            nome=model.nome,
            categoria=model.categoria,
            start_date=model.start_date,
            end_date=model.end_date,
            limite=limite,
            _ativo=model._ativo,
            lancamentos=lancamentos,
            created_at=model.created_at,
        )
    
    def get(self, budget_id: str) -> Optional[Budget]:
        """Retrieve a budget by its ID."""
        session = self._create_session()
        try:
            result = session.execute(
                select(BudgetModel).where(BudgetModel.id == budget_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._model_to_budget(model)
        finally:
            session.close()
    
    def save(self, budget: Budget) -> None:
        """Save a budget."""
        session = self._create_session()
        try:
            # Check if budget already exists
            existing = self.get(budget.id)
            
            if existing is None:
                # New budget - insert
                model = self._budget_to_model(budget)
                session.add(model)
            else:
                # Existing budget - update
                # Delete existing lancamentos first
                session.execute(
                    LancamentoModel.__table__.delete().where(
                        LancamentoModel.budget_id == budget.id
                    )
                )
                
                # Update budget fields
                model = session.get(BudgetModel, budget.id)
                model.nome = budget.nome
                model.categoria = budget.categoria
                model.start_date = budget.start_date
                model.end_date = budget.end_date
                model.limite_amount = float(budget.limite.amount)
                model.limite_currency = budget.limite.currency
                model._ativo = budget._ativo
                model.created_at = budget.created_at
                
                # Add new lancamentos
                for l in budget.lancamentos:
                    lanc_model = LancamentoModel(
                        id=l.id,
                        budget_id=l.budget_id,
                        valor_amount=float(l.valor.amount),
                        valor_currency=l.valor.currency,
                        data=l.data,
                        descricao=l.descricao,
                        tipo=l.tipo,
                        categoria=l.categoria,
                        conta=l.conta,
                        metodo_pagamento=l.metodo_pagamento,
                        pendente=l.pendente,
                        data_criacao=l.data_criacao,
                    )
                    session.add(lanc_model)
            
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def list_by_user_id(
        self, user_id: str, ativo: Optional[bool] = True
    ) -> List[Budget]:
        """
        List budgets for a given user.
        If ativo is True, return only active budgets.
        If ativo is False, return only inactive budgets.
        If ativo is None, return all budgets (active and inactive).
        """
        session = self._create_session()
        try:
            if ativo is None:
                query = select(BudgetModel).where(BudgetModel.user_id == user_id)
            else:
                query = select(BudgetModel).where(
                    and_(
                        BudgetModel.user_id == user_id,
                        BudgetModel._ativo == ativo
                    )
                )
            
            result = session.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_budget(m) for m in models]
        finally:
            session.close()
