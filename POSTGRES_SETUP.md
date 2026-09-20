# PostgreSQL Setup for Yeldify API

## Overview

This project now supports **PostgreSQL** as the database backend. The repository can be switched between InMemory (default) and PostgreSQL using environment variables.

## Prerequisites

- PostgreSQL server (local or remote)
- Python 3.11+

## Installation

### 1. Install dependencies

```bash
pip install -r requirements/base.txt
```

### 2. Set up PostgreSQL

#### Option A: Local PostgreSQL with Docker

```bash
# Start PostgreSQL container
docker run --name yeldify-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=yeldify \
  -p 5432:5432 \
  -d postgres:16
```

#### Option B: Local PostgreSQL (native)

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create user and database
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "CREATE DATABASE yeldify;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE yeldify TO postgres;"
```

### 3. Initialize database tables

```bash
# Create tables
python scripts/init_db.py

# Or recreate (drop + create)
python scripts/init_db.py --recreate

# Or drop all tables (DANGEROUS!)
python scripts/init_db.py --drop
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/yeldify` | PostgreSQL connection string |
| `USE_POSTGRES` | `false` | Set to `true` to use PostgreSQL instead of InMemory |

### Example .env file

```env
# Use PostgreSQL
USE_POSTGRES=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/yeldify
```

### Connection String Formats

```
# Basic
postgresql://user:password@localhost:5432/database

# With async (if using asyncpg)
postgresql+asyncpg://user:password@localhost:5432/database

# Remote
postgresql://user:password@host:port/database
```

## Running the API

### With PostgreSQL

```bash
# Set environment variables
export USE_POSTGRES=true
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/yeldify

# Start API
uvicorn src.infrastructure.web.api.v1.api:app --reload
```

### With InMemory (default)

```bash
# No environment variables needed
uvicorn src.infrastructure.web.api.v1.api:app --reload
```

## Database Schema

### Tables

#### budgets

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR | Primary key, budget ID |
| user_id | VARCHAR | User ID (foreign key) |
| nome | VARCHAR | Budget name |
| categoria | VARCHAR | Budget category |
| start_date | DATE | Start date |
| end_date | DATE | End date |
| limite_amount | NUMERIC(12,2) | Planned limit amount |
| limite_currency | VARCHAR(3) | Currency (default: BRL) |
| _ativo | BOOLEAN | Active status |
| created_at | DATE | Creation date |

#### lancamentos

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR | Primary key, transaction ID |
| budget_id | VARCHAR | Budget ID (foreign key) |
| valor_amount | NUMERIC(12,2) | Transaction amount |
| valor_currency | VARCHAR(3) | Currency (default: BRL) |
| data | DATE | Transaction date |
| descricao | VARCHAR | Description |
| tipo | ENUM | Transaction type (ENTRADA/SAIDA) |

## Troubleshooting

### Connection Error

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server
```

**Solution:** Verify PostgreSQL is running and credentials are correct.

```bash
# Test connection
psql -h localhost -U postgres -d yeldify
```

### Table Already Exists

```
sqlalchemy.exc.ProgrammingError: relation "budgets" already exists
```

**Solution:** Use `--recreate` or `--drop` first.

```bash
python scripts/init_db.py --recreate
```

### Missing Dependencies

```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution:** Install required packages.

```bash
pip install psycopg2-binary sqlalchemy
```

## Migration from InMemory to PostgreSQL

1. Start with InMemory (default)
2. Create your budgets via API
3. Switch to PostgreSQL by setting `USE_POSTGRES=true`
4. Initialize tables with `python scripts/init_db.py`
5. Restart the API - existing data will be in PostgreSQL

**Note:** InMemory data is **not migrated automatically**. When you switch to PostgreSQL, start with an empty database.

## Files Created/Modified

### New Files
- `src/infrastructure/persistence/database.py` - SQLAlchemy Base
- `src/infrastructure/persistence/models.py` - SQLAlchemy models
- `src/infrastructure/persistence/postgres_sync_budget_repository.py` - PostgreSQL sync repository
- `src/infrastructure/persistence/repository_factory.py` - Repository factory
- `scripts/init_db.py` - Database initialization script
- `.env.example` - Environment variables template

### Modified Files
- `requirements/base.txt` - Added PostgreSQL dependencies
- `src/infrastructure/web/api/v1/dependencies.py` - Uses repository factory
