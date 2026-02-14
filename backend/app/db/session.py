from typing import AsyncGenerator, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from app.core.config import settings
from app.db.pgbouncer import get_pgbouncer_connect_args

# Create async engine (pgbouncer-safe for Supabase transaction pool mode)
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    connect_args=get_pgbouncer_connect_args(),
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_rls(
    firm_id: UUID,
    user_id: Optional[UUID] = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with RLS context set.

    This ensures all queries are automatically filtered to the specified firm.
    Use this for any operation that needs firm isolation.
    """
    async with async_session_maker() as session:
        try:
            # Set RLS context (SET does not accept bind params; UUIDs are safe to interpolate)
            await session.execute(text(f"SET app.current_firm_id = '{firm_id}'"))
            if user_id:
                await session.execute(text(f"SET app.current_user_id = '{user_id}'"))

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Clear RLS context
            await session.execute(text("RESET app.current_firm_id"))
            await session.execute(text("RESET app.current_user_id"))
            await session.close()


async def init_db():
    """Initialize database tables and extensions."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def run_rls_migrations():
    """Run RLS migration scripts."""
    import os
    from pathlib import Path

    migrations_dir = Path(__file__).parent / "migrations"

    async with engine.begin() as conn:
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            with open(migration_file) as f:
                sql = f.read()
                # Split by semicolons and execute each statement
                for statement in sql.split(";"):
                    statement = statement.strip()
                    if statement and not statement.startswith("--"):
                        try:
                            await conn.execute(text(statement))
                        except Exception as e:
                            # Log but continue - some statements may already be applied
                            print(f"Migration statement warning: {e}")
