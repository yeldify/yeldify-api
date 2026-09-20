#!/usr/bin/env python
"""
Seed demo data for the Yeldify API (desenvolvimento).

Popula o repositório (in-memory ou PostgreSQL, conforme USE_POSTGRES) com
orçamentos e lançamentos de exemplo.

Usage:
    python scripts/seed_demo.py [--force]
"""
import os
import sys
from pathlib import Path

# Garante que o diretório raiz da API esteja no sys.path (permite rodar de qualquer lugar)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.persistence.repository_factory import create_repository
from src.infrastructure.persistence.seed import DEFAULT_USER_ID, seed_demo


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed demo data para a Yeldify API")
    parser.add_argument("--force", action="store_true",
                        help="Reaplica os seeds mesmo se já existirem dados")
    args = parser.parse_args()

    repo = create_repository()
    if seed_demo(repo, user_id=DEFAULT_USER_ID, force=args.force):
        print(f"✓ Seeds aplicados para {DEFAULT_USER_ID}.")
        for b in repo.list_by_user_id(DEFAULT_USER_ID, ativo=None):
            print(f"  - {b.nome} (ativo={b.ativo}, {len(b.lancamentos)} lançamentos)")
    else:
        print(f"Dados já existentes para {DEFAULT_USER_ID}. Use --force para reaplicar.")


if __name__ == "__main__":
    main()