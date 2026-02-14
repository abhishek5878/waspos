"""
Vector Store with Row Level Security (RLS) Enforcement.

This module provides vector storage and similarity search with guaranteed
firm isolation. All queries are filtered by firm_id to ensure no cross-firm
data leakage, even in vector similarity searches.

SECURITY GUARANTEES:
1. All vector searches are filtered by firm_id at the SQL level
2. RLS policies provide a second layer of defense
3. The secure_vector_search function uses SECURITY DEFINER for additional isolation
4. Audit logging tracks all vector search operations
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.document import DocumentChunk
from app.services.memory.embeddings import EmbeddingService
from app.core.config import settings

logger = structlog.get_logger()


class VectorStore:
    """
    Vector storage and similarity search using pgvector with RLS enforcement.

    All operations are automatically scoped to the specified firm_id.
    Cross-firm data access is impossible at the application and database level.
    """

    def __init__(self, db: AsyncSession, firm_id: UUID):
        self.db = db
        self.firm_id = firm_id
        self.embedding_service = EmbeddingService()
        self.logger = logger.bind(service="vector_store", firm_id=str(firm_id))

    async def _set_rls_context(self) -> None:
        """Set the RLS context for the current session."""
        await self.db.execute(
            text("SET app.current_firm_id = :firm_id"),
            {"firm_id": str(self.firm_id)}
        )

    async def add_chunks(
        self,
        document_id: UUID,
        chunks: list[dict],
    ) -> list[DocumentChunk]:
        """Add document chunks with embeddings to the vector store."""
        self.logger.info("adding_chunks", document_id=str(document_id), count=len(chunks))

        # Ensure RLS context is set
        await self._set_rls_context()

        # Generate embeddings for all chunks
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedding_service.embed_texts(texts)

        # Create chunk records with firm_id for RLS
        chunk_records = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_record = DocumentChunk(
                document_id=document_id,
                firm_id=self.firm_id,  # Critical for RLS
                content=chunk["content"],
                chunk_index=chunk["chunk_index"],
                page_number=chunk.get("page_number"),
                section_type=chunk.get("section_type"),
                embedding=embedding,
                metadata=chunk.get("metadata"),
            )
            chunk_records.append(chunk_record)
            self.db.add(chunk_record)

        await self.db.flush()
        self.logger.info("chunks_added", count=len(chunk_records))
        return chunk_records

    async def similarity_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        document_id: Optional[UUID] = None,
        document_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for similar chunks using cosine similarity with RLS enforcement.

        SECURITY: This method explicitly filters by firm_id AND relies on RLS
        policies as a defense-in-depth measure. Even if the firm_id filter
        were somehow bypassed, RLS would prevent cross-firm access.
        """
        self.logger.info(
            "similarity_search",
            query=query[:50],
            limit=limit,
            firm_id=str(self.firm_id),
        )

        # Set RLS context for additional security
        await self._set_rls_context()

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        query_vector = f"[{','.join(map(str, query_embedding))}]"

        # Build secure query with explicit firm_id filter
        # The firm_id filter is the primary security mechanism
        # RLS policies provide defense-in-depth
        sql = text("""
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                dc.chunk_index,
                dc.page_number,
                dc.section_type,
                d.original_filename as document_title,
                d.deal_id,
                1 - (dc.embedding <=> :query_vector::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.firm_id = :firm_id  -- Primary security filter
            AND d.firm_id = :firm_id      -- Double-check on joined table
            {doc_filter}
            {type_filter}
            AND 1 - (dc.embedding <=> :query_vector::vector) >= :min_similarity
            ORDER BY dc.embedding <=> :query_vector::vector
            LIMIT :limit
        """.format(
            doc_filter="AND dc.document_id = :document_id" if document_id else "",
            type_filter="AND d.document_type = :document_type" if document_type else "",
        ))

        params = {
            "query_vector": query_vector,
            "firm_id": str(self.firm_id),
            "min_similarity": min_similarity,
            "limit": limit,
        }
        if document_id:
            params["document_id"] = str(document_id)
        if document_type:
            params["document_type"] = document_type

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        self.logger.info(
            "similarity_search_complete",
            results=len(rows),
            firm_id=str(self.firm_id),
        )

        return [
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "deal_id": row.deal_id,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "page_number": row.page_number,
                "section_type": row.section_type,
                "document_title": row.document_title,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]

    async def secure_similarity_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> list[dict]:
        """
        Perform similarity search using the secure_vector_search SQL function.

        This method uses a SECURITY DEFINER function that enforces RLS
        at the database level, providing the strongest isolation guarantee.
        """
        self.logger.info(
            "secure_similarity_search",
            query=query[:50],
            firm_id=str(self.firm_id),
        )

        # Set RLS context
        await self._set_rls_context()

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        query_vector = f"[{','.join(map(str, query_embedding))}]"

        # Use the secure function defined in RLS migration
        result = await self.db.execute(
            text("""
                SELECT * FROM secure_vector_search(
                    :query_vector::vector,
                    :threshold,
                    :limit
                )
            """),
            {
                "query_vector": query_vector,
                "threshold": min_similarity,
                "limit": limit,
            }
        )

        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "similarity": float(row.similarity),
            }
            for row in result.fetchall()
        ]

    async def search_historical_memos(
        self,
        query: str,
        limit: int = 10,
        exclude_deal_id: Optional[UUID] = None,
    ) -> list[dict]:
        """
        Search historical IC memos for contradiction/ghost loss detection.

        This searches only within the current firm's historical memos,
        ensuring no cross-firm data leakage.
        """
        self.logger.info(
            "search_historical_memos",
            query=query[:50],
            firm_id=str(self.firm_id),
        )

        return await self.similarity_search(
            query=query,
            limit=limit,
            document_type="ic_memo",
            min_similarity=0.6,
        )

    async def search_pass_patterns(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search for historical "Pass" patterns in memos.

        Used by the Ghost Loss Analyzer to find historical pass decisions
        that might be relevant to current deals.
        """
        self.logger.info(
            "search_pass_patterns",
            query=query[:50],
            firm_id=str(self.firm_id),
        )

        # Set RLS context
        await self._set_rls_context()

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        query_vector = f"[{','.join(map(str, query_embedding))}]"

        # Search for pass-related content
        sql = text("""
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                d.original_filename as document_title,
                d.extracted_company as company_name,
                1 - (dc.embedding <=> :query_vector::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.firm_id = :firm_id
            AND d.firm_id = :firm_id
            AND d.document_type = 'ic_memo'
            AND (
                LOWER(dc.content) LIKE '%pass%'
                OR LOWER(dc.content) LIKE '%concern%'
                OR LOWER(dc.content) LIKE '%risk%'
                OR LOWER(dc.content) LIKE '%not invest%'
                OR LOWER(dc.content) LIKE '%decline%'
                OR LOWER(dc.content) LIKE '%red flag%'
            )
            AND 1 - (dc.embedding <=> :query_vector::vector) >= 0.5
            ORDER BY dc.embedding <=> :query_vector::vector
            LIMIT :limit
        """)

        result = await self.db.execute(
            sql,
            {
                "query_vector": query_vector,
                "firm_id": str(self.firm_id),
                "limit": limit,
            }
        )

        return [
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "document_title": row.document_title,
                "company_name": row.company_name,
                "similarity": float(row.similarity),
            }
            for row in result.fetchall()
        ]

    async def delete_document_chunks(self, document_id: UUID) -> int:
        """
        Delete all chunks for a document.

        RLS ensures only chunks belonging to the current firm can be deleted.
        """
        await self._set_rls_context()

        result = await self.db.execute(
            text("""
                DELETE FROM document_chunks
                WHERE document_id = :document_id
                AND firm_id = :firm_id
                RETURNING id
            """),
            {
                "document_id": str(document_id),
                "firm_id": str(self.firm_id),
            }
        )

        deleted_count = len(result.fetchall())
        self.logger.info(
            "chunks_deleted",
            document_id=str(document_id),
            count=deleted_count,
        )
        return deleted_count
