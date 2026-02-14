"""
Ghost Loss Analyzer - Searches historical "Pass" decisions to surface potential blind spots.

A "Ghost Loss" is a deal we passed on that went on to become a massive success.
This module searches our institutional memory to find patterns that might indicate
we're about to make the same mistake again.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from anthropic import Anthropic
import structlog

from app.core.config import settings
from app.models.deal import Deal, DealStage
from app.models.document import DocumentChunk
from app.services.memory.embeddings import EmbeddingService

logger = structlog.get_logger()


class GhostLossAnalyzer:
    """
    Analyze historical pass decisions to identify potential "Ghost Loss" patterns.

    This is the institutional conscience of the firm - it surfaces uncomfortable
    truths about deals we passed on that match patterns in new opportunities.
    """

    def __init__(self, db: AsyncSession, firm_id: UUID):
        self.db = db
        self.firm_id = firm_id
        self.embedding_service = EmbeddingService()
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.logger = logger.bind(service="ghost_loss_analyzer", firm_id=str(firm_id))

    async def find_ghost_loss_patterns(
        self,
        deal: Deal,
        limit: int = 10,
        lookback_days: int = 1095,  # 3 years
    ) -> list[dict]:
        """
        Search for historical "Pass" patterns that match the current deal.

        This searches:
        1. Deals we explicitly passed on with documented reasons
        2. IC memo sections discussing why we passed on similar companies
        3. Semantic similarity between current deal and historical passes
        """
        self.logger.info(
            "searching_ghost_loss_patterns",
            deal_id=str(deal.id),
            company=deal.company_name,
        )

        patterns = []

        # 1. Search for explicitly passed deals with similar characteristics
        passed_deals = await self._find_similar_passed_deals(deal, limit=limit)
        patterns.extend(passed_deals)

        # 2. Search vector store for "pass" related content
        vector_patterns = await self._search_pass_vectors(deal, limit=limit)
        patterns.extend(vector_patterns)

        # 3. Deduplicate and rank by relevance
        patterns = self._deduplicate_and_rank(patterns)

        self.logger.info(
            "ghost_loss_patterns_found",
            count=len(patterns),
            deal_id=str(deal.id),
        )

        return patterns[:limit]

    async def _find_similar_passed_deals(
        self,
        deal: Deal,
        limit: int = 5,
    ) -> list[dict]:
        """Find deals we passed on that are similar to the current deal."""
        # Query for passed deals in similar sectors
        query = select(Deal).where(
            Deal.firm_id == self.firm_id,
            Deal.stage == DealStage.PASSED,
            Deal.pass_reason.isnot(None),
        )

        # Filter by sector if available
        if deal.sector:
            query = query.where(Deal.sector == deal.sector)

        query = query.order_by(Deal.updated_at.desc()).limit(limit * 2)

        result = await self.db.execute(query)
        passed_deals = result.scalars().all()

        if not passed_deals:
            return []

        # Generate embedding for current deal
        deal_text = f"{deal.company_name} {deal.one_liner or ''} {deal.description or ''} {deal.sector or ''}"
        deal_embedding = self.embedding_service.embed_text(deal_text)

        # Score similarity for each passed deal
        scored_deals = []
        for passed_deal in passed_deals:
            passed_text = f"{passed_deal.company_name} {passed_deal.one_liner or ''} {passed_deal.description or ''}"
            passed_embedding = self.embedding_service.embed_text(passed_text)
            similarity = self.embedding_service.compute_similarity(deal_embedding, passed_embedding)

            if similarity > 0.5:  # Only include reasonably similar deals
                scored_deals.append({
                    "type": "passed_deal",
                    "deal_id": str(passed_deal.id),
                    "company_name": passed_deal.company_name,
                    "sector": passed_deal.sector,
                    "pass_reason": passed_deal.pass_reason,
                    "pass_date": passed_deal.updated_at.isoformat() if passed_deal.updated_at else None,
                    "similarity": similarity,
                    "one_liner": passed_deal.one_liner,
                    "asking_valuation": float(passed_deal.asking_valuation) if passed_deal.asking_valuation else None,
                })

        # Sort by similarity
        scored_deals.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_deals[:limit]

    async def _search_pass_vectors(
        self,
        deal: Deal,
        limit: int = 5,
    ) -> list[dict]:
        """Search vector store for historical content about passing on similar deals."""
        # Build search queries that target "pass" related content
        search_queries = [
            f"why we passed on {deal.sector} deals",
            f"concerns about {deal.sector} investments",
            f"red flags {deal.one_liner or deal.company_name}",
            f"pass recommendation {deal.sector}",
        ]

        all_results = []
        deal_text = f"{deal.company_name} {deal.one_liner or ''} {deal.sector or ''}"
        query_embedding = self.embedding_service.embed_text(deal_text)

        # Search for pass-related content in historical memos
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
            AND d.document_type = 'ic_memo'
            AND (
                LOWER(dc.content) LIKE '%pass%'
                OR LOWER(dc.content) LIKE '%concern%'
                OR LOWER(dc.content) LIKE '%risk%'
                OR LOWER(dc.content) LIKE '%not invest%'
                OR LOWER(dc.content) LIKE '%decline%'
            )
            AND 1 - (dc.embedding <=> :query_vector::vector) >= 0.5
            ORDER BY dc.embedding <=> :query_vector::vector
            LIMIT :limit
        """)

        query_vector = f"[{','.join(map(str, query_embedding))}]"

        try:
            result = await self.db.execute(
                sql,
                {
                    "query_vector": query_vector,
                    "firm_id": str(self.firm_id),
                    "limit": limit,
                }
            )
            rows = result.fetchall()

            for row in rows:
                # Extract the most relevant "pass reason" from the content
                pass_reason = self._extract_pass_reason(row.content)

                all_results.append({
                    "type": "historical_memo",
                    "chunk_id": str(row.id),
                    "document_id": str(row.document_id),
                    "company_name": row.company_name or row.document_title,
                    "sector": None,
                    "pass_reason": pass_reason,
                    "pass_date": None,
                    "similarity": float(row.similarity),
                    "source_content": row.content[:500],
                })
        except Exception as e:
            self.logger.error("vector_search_error", error=str(e))

        return all_results

    def _extract_pass_reason(self, content: str) -> str:
        """Extract the core pass reason from memo content."""
        # Look for common patterns in pass reasoning
        import re

        # Try to find explicit pass reasons
        patterns = [
            r"pass(?:ed|ing)?\s+(?:on\s+)?(?:this\s+)?(?:deal\s+)?(?:because|due to|as)\s+(.{50,300})",
            r"recommend(?:ation)?\s*:?\s*pass\s*[.\-:]\s*(.{50,300})",
            r"concerns?\s*(?:include|are|:)\s*(.{50,300})",
            r"(?:key\s+)?risks?\s*(?:include|are|:)\s*(.{50,300})",
            r"not\s+(?:recommend|proceed|invest)\s+(?:because|due to)\s*(.{50,300})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: return first 200 chars with "..." context
        return content[:200].strip() + "..."

    def _deduplicate_and_rank(self, patterns: list[dict]) -> list[dict]:
        """Deduplicate patterns and rank by relevance."""
        seen_companies = set()
        unique_patterns = []

        for pattern in sorted(patterns, key=lambda x: x.get("similarity", 0), reverse=True):
            company = pattern.get("company_name", "").lower()
            if company and company not in seen_companies:
                seen_companies.add(company)
                unique_patterns.append(pattern)
            elif not company:
                unique_patterns.append(pattern)

        return unique_patterns

    async def generate_counter_thesis(
        self,
        deal: Deal,
        patterns: list[dict],
    ) -> str:
        """Generate a specific counter-thesis based on ghost loss patterns."""
        if not patterns:
            return ""

        pattern_summary = "\n".join([
            f"- {p.get('company_name', 'Unknown')}: {p.get('pass_reason', 'No reason documented')}"
            for p in patterns[:5]
        ])

        prompt = f"""You are a contrarian VC analyst. Based on these historical pass patterns from our firm, write a 2-paragraph counter-thesis for why we might be making a mistake if we pass on {deal.company_name}.

CURRENT DEAL: {deal.company_name}
ONE-LINER: {deal.one_liner or 'Not provided'}
SECTOR: {deal.sector or 'Unknown'}

HISTORICAL PASS PATTERNS:
{pattern_summary}

Write a brutally honest counter-thesis that:
1. Identifies which historical biases might be at play
2. Explains why this deal might be different from our pattern-matched concerns
3. Names specific things that could make us regret passing

Be specific and uncomfortable. This should challenge groupthink."""

        response = self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text
