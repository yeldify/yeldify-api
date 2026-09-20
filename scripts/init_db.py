#!/usr/bin/env python
"""
Script to initialize PostgreSQL database for Yeldify API.
Creates tables and optionally populates with sample data.

Usage:
    python scripts/init_db.py

Environment variables:
    DATABASE_URL: PostgreSQL connection string (default: postgresql://postgres:postgres@localhost:5432/yeldify)
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import models to register tables
from src.infrastructure.persistence.models import BudgetModel, LancamentoModel
from src.infrastructure.persistence.database import Base


def get_db_url() -> str:
    """Get database URL from environment or use default."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/yeldify")
    # Replace asyncpg with psycopg2 for sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    return db_url


def create_tables():
    """Create all database tables."""
    db_url = get_db_url()
    engine = create_engine(db_url, echo=True)
    
    print(f"Creating tables on: {db_url}")
    print("Tables to create: budgets, lancamentos")
    
    # Create all tables
    Base.metadata.create_all(engine)
    print("✓ Tables created successfully!")


def drop_tables():
    """Drop all database tables (DANGEROUS!)."""
    import sys
    
    print("⚠️  WARNING: This will drop all tables and data!")
    print("Type 'yes' to continue or anything else to cancel:")
    
    response = input().strip().lower()
    if response != 'yes':
        print("Cancelled.")
        sys.exit(0)
    
    db_url = get_db_url()
    engine = create_engine(db_url, echo=True)
    
    print(f"Dropping tables on: {db_url}")
    Base.metadata.drop_all(engine)
    print("✓ Tables dropped successfully!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL database for Yeldify API")
    parser.add_argument("--drop", action="store_true", help="Drop all tables (DANGEROUS!)")
    parser.add_argument("--create", action="store_true", help="Create all tables (default)")
    parser.add_argument("--recreate", action="store_true", help="Drop and then create tables")
    
    args = parser.parse_args()
    
    if args.recreate:
        drop_tables()
        create_tables()
    elif args.drop:
        drop_tables()
    else:
        create_tables()


if __name__ == "__main__":
    main()
