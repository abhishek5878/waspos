#!/usr/bin/env python3
"""
Run database migrations without needing psql/createdb.

Creates tables (init_db), then runs migration SQL files 002 and 003.
Use when PostgreSQL is running but you don't have psql in PATH.

Usage (from project root):
  PYTHONPATH=backend:. python3 scripts/run_migrations.py [--db-url URL]

To create the database first (if using local Postgres):
  Python one-liner (connect to default 'postgres' DB first):
  python3 -c "
  import asyncio
  import asyncpg
  async def create():
      c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
      await c.execute('CREATE DATABASE wasp_os')
      await c.close()
  asyncio.run(create())
  "
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.pgbouncer import get_pgbouncer_connect_args
from app.db.session import Base

# Import all models so they register with Base.metadata before create_all
import app.models  # noqa: F401


async def main(db_url: str):
    engine = create_async_engine(db_url, connect_args=get_pgbouncer_connect_args())
    migrations_dir = Path(__file__).parent.parent / "backend" / "app" / "db" / "migrations"

    async with engine.begin() as conn:
        print("Creating extension and tables...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

        for name in ("002_add_friction_gp_bias_columns.sql", "003_rename_chunk_metadata.sql"):
            path = migrations_dir / name
            if not path.exists():
                continue
            print(f"Running {name}...")
            sql = path.read_text()
            # Run whole file as one unit to preserve DO $$ ... $$ blocks
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            if "$$" in sql:
                # File contains dollar-quoted block - run entire file at once
                try:
                    await conn.execute(text(sql))
                except Exception as e:
                    print(f"  Warning: {e}")
            else:
                for statement in statements:
                    try:
                        await conn.execute(text(statement + ";"))
                    except Exception as e:
                        print(f"  Warning: {e}")

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run DB migrations (tables + 002, 003). Requires PostgreSQL running."
    )
    parser.add_argument(
        "--db-url",
        default=settings.DATABASE_URL,
        help="Full URL, e.g. postgresql+asyncpg://USER:PASSWORD@HOST:5432/wasp_os",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.db_url))
    except OSError as e:
        err = str(e).lower()
        if "5432" in str(e) and ("61" in err or "connect call failed" in err):
            print("Cannot connect to PostgreSQL (connection refused).")
            print("  - Start Postgres locally (e.g. Postgres.app, Homebrew), or")
            print("  - Use a cloud DB and pass --db-url with real USER, PASSWORD, HOST.")
            print("  Example: --db-url 'postgresql+asyncpg://user:pass@db.xxx.supabase.co:5432/postgres'")
        elif "nodename nor servname" in err or "gaierror" in err:
            print("Invalid database host in DATABASE_URL or --db-url.")
            print("  Replace placeholders with real values: USER, PASSWORD, HOST (e.g. db.xxx.supabase.co).")
        raise
