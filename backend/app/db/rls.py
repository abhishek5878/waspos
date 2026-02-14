"""
Row Level Security (RLS) utilities for Supabase integration.

This module provides utilities to set the current firm context for RLS policies.
When using Supabase with RLS enabled, every database query is automatically
filtered to only return data from the current user's firm.
"""

from contextlib import asynccontextmanager
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


async def set_firm_context(
    db: AsyncSession,
    firm_id: UUID,
    user_id: UUID | None = None,
) -> None:
    """
    Set the current firm and user context for RLS policies.

    This must be called at the start of every request to ensure
    RLS policies correctly filter data to the current firm.

    Args:
        db: The database session
        firm_id: The UUID of the current firm
        user_id: The UUID of the current user (optional)
    """
    await db.execute(
        text("SET app.current_firm_id = :firm_id"),
        {"firm_id": str(firm_id)}
    )

    if user_id:
        await db.execute(
            text("SET app.current_user_id = :user_id"),
            {"user_id": str(user_id)}
        )

    logger.debug("rls_context_set", firm_id=str(firm_id), user_id=str(user_id) if user_id else None)


async def clear_firm_context(db: AsyncSession) -> None:
    """
    Clear the firm context after a request completes.
    """
    await db.execute(text("RESET app.current_firm_id"))
    await db.execute(text("RESET app.current_user_id"))


@asynccontextmanager
async def firm_context(
    db: AsyncSession,
    firm_id: UUID,
    user_id: UUID | None = None,
):
    """
    Context manager to automatically set and clear firm context.

    Usage:
        async with firm_context(db, firm_id, user_id):
            # All queries here are automatically filtered to this firm
            deals = await db.execute(select(Deal))
    """
    try:
        await set_firm_context(db, firm_id, user_id)
        yield
    finally:
        await clear_firm_context(db)


class RLSMiddleware:
    """
    FastAPI middleware to automatically set RLS context from JWT claims.

    This middleware extracts the firm_id and user_id from the JWT token
    and sets them in the database session for RLS filtering.
    """

    def __init__(self, db_session_maker):
        self.db_session_maker = db_session_maker

    async def __call__(self, request, call_next):
        # Extract firm_id from JWT (this would come from your auth system)
        firm_id = request.state.get("firm_id")
        user_id = request.state.get("user_id")

        if firm_id:
            async with self.db_session_maker() as db:
                await set_firm_context(db, firm_id, user_id)

        response = await call_next(request)
        return response


# Dependency for FastAPI routes
async def get_db_with_rls(
    db: AsyncSession,
    current_user: dict,
) -> AsyncSession:
    """
    FastAPI dependency that provides a database session with RLS context set.

    Usage:
        @router.get("/deals")
        async def list_deals(
            db: AsyncSession = Depends(get_db_with_rls),
        ):
            # RLS is automatically enforced
            result = await db.execute(select(Deal))
            return result.scalars().all()
    """
    firm_id = current_user.get("firm_id")
    user_id = current_user.get("user_id")

    if firm_id:
        await set_firm_context(db, UUID(firm_id), UUID(user_id) if user_id else None)

    return db


# Vector search with RLS
async def secure_vector_search(
    db: AsyncSession,
    query_embedding: list[float],
    firm_id: UUID,
    match_threshold: float = 0.7,
    match_count: int = 10,
) -> list[dict]:
    """
    Perform vector similarity search with RLS enforcement.

    This function ensures that vector search results are always
    filtered to the current firm, even when using raw SQL for
    performance reasons.

    Args:
        db: Database session
        query_embedding: The query vector
        firm_id: The firm to search within
        match_threshold: Minimum similarity score (0-1)
        match_count: Maximum number of results

    Returns:
        List of matching document chunks with similarity scores
    """
    # Ensure firm context is set
    await set_firm_context(db, firm_id)

    # Use the secure_vector_search function defined in SQL
    query_vector = f"[{','.join(map(str, query_embedding))}]"

    result = await db.execute(
        text("""
            SELECT * FROM secure_vector_search(
                :query_vector::vector,
                :threshold,
                :limit
            )
        """),
        {
            "query_vector": query_vector,
            "threshold": match_threshold,
            "limit": match_count,
        }
    )

    return [
        {
            "id": row.id,
            "document_id": row.document_id,
            "content": row.content,
            "similarity": row.similarity,
        }
        for row in result.fetchall()
    ]


# Verification utilities
async def verify_rls_enabled(db: AsyncSession) -> dict:
    """
    Verify that RLS is properly enabled on all tables.

    Returns a dict mapping table names to their RLS status.
    """
    result = await db.execute(
        text("""
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN (
                'firms', 'users', 'deals', 'documents',
                'document_chunks', 'investment_memos',
                'memo_templates', 'conviction_polls', 'poll_votes'
            )
        """)
    )

    return {row.tablename: row.rowsecurity for row in result.fetchall()}


async def test_cross_firm_isolation(
    db: AsyncSession,
    firm_a_id: UUID,
    firm_b_id: UUID,
) -> bool:
    """
    Test that RLS properly isolates data between firms.

    Returns True if isolation is working correctly.
    """
    from app.models.deal import Deal

    # Set context to Firm A
    await set_firm_context(db, firm_a_id)

    # Try to query - should only see Firm A data
    result_a = await db.execute(
        text("SELECT firm_id FROM deals LIMIT 10")
    )
    firms_seen_a = set(row.firm_id for row in result_a.fetchall())

    # Set context to Firm B
    await set_firm_context(db, firm_b_id)

    # Try to query - should only see Firm B data
    result_b = await db.execute(
        text("SELECT firm_id FROM deals LIMIT 10")
    )
    firms_seen_b = set(row.firm_id for row in result_b.fetchall())

    # Verify isolation
    a_sees_only_a = all(f == firm_a_id for f in firms_seen_a) if firms_seen_a else True
    b_sees_only_b = all(f == firm_b_id for f in firms_seen_b) if firms_seen_b else True
    no_cross_contamination = not (firms_seen_a & firms_seen_b)

    return a_sees_only_a and b_sees_only_b and no_cross_contamination
