"""
Factory for creating repository instances.
Allows switching between InMemory and PostgreSQL implementations.
"""
import os
from typing import Optional
from src.infrastructure.persistence.repositories import IBudgetRepository
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository

# Use environment variable to decide which repository to use
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"

# Optional import for PostgreSQL (only if dependencies are installed)
try:
    from src.infrastructure.persistence.postgres_sync_budget_repository import PostgresSyncBudgetRepository
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    PostgresSyncBudgetRepository = None

# Singleton: sem esta cache, um repositório in-memory novo é criado a cada
# request e os dados se perdem entre requisições (a API ficaria inutilizável).
_singleton_repo = None


def create_repository() -> IBudgetRepository:
    """
    Create a repository instance based on configuration.
    
    Uses USE_POSTGRES environment variable to decide:
    - If USE_POSTGRES=true and dependencies are available: returns PostgresSyncBudgetRepository
    - Otherwise: returns InMemoryBudgetRepository
    The instance is cached (singleton) so state survives between requests.
    
    Returns:
        IBudgetRepository: Repository instance (InMemory or PostgreSQL)
    """
    global _singleton_repo
    if _singleton_repo is None:
        if USE_POSTGRES and POSTGRES_AVAILABLE:
            _singleton_repo = PostgresSyncBudgetRepository()
        else:
            # Default: InMemory
            _singleton_repo = InMemoryBudgetRepository()
    return _singleton_repo
