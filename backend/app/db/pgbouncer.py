"""
Pgbouncer-safe connection setup for asyncpg + Supabase (transaction pool mode).

When using pgbouncer with pool_mode "transaction" or "statement", prepared
statements cause DuplicatePreparedStatementError because pgbouncer reuses
connections across transactions. Use the connect_args returned by
get_pgbouncer_connect_args() when creating async engines.

Reference: https://github.com/sqlalchemy/sqlalchemy/issues/6467
"""

from uuid import uuid4

from asyncpg import Connection


class PgbouncerSafeConnection(Connection):
    """
    asyncpg Connection subclass that generates unique prepared statement IDs.

    The default asyncpg Connection uses a global counter (_uid) for statement
    names, causing collisions when pgbouncer returns connections from different
    transactions/sessions. Using UUIDs ensures each prepared statement has a
    unique name across the connection pool.
    """

    def _get_unique_id(self, prefix: str) -> str:
        return f"__asyncpg_{prefix}_{uuid4()}__"


def get_pgbouncer_connect_args() -> dict:
    """
    Connect args for create_async_engine when using pgbouncer (Supabase pooler).

    Usage:
        engine = create_async_engine(
            db_url,
            connect_args=get_pgbouncer_connect_args(),
        )
    """
    return {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "connection_class": PgbouncerSafeConnection,
    }
