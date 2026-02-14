from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from anthropic import Anthropic
import structlog

from app.core.config import settings
from app.services.memory.vector_store import VectorStore
from app.schemas.memo import ContradictionFlag

logger = structlog.get_logger()


CONTRADICTION_PROMPT = """You are analyzing a new IC memo against historical investment decisions.

CURRENT MEMO SECTION ({section_name}):
{current_content}

HISTORICAL MEMO ({historical_title}):
{historical_content}

Does the current memo make claims or take positions that CONTRADICT the reasoning in the historical memo?

Focus on:
1. Market sizing contradictions (e.g., saying a market is large now but called it small before)
2. Team assessment contradictions (e.g., valuing a background now that was discounted before)
3. Competitive moat contradictions (e.g., believing a moat exists that was dismissed before)
4. Business model contradictions (e.g., supporting a model previously rejected)

If you find a contradiction, respond with JSON:
```json
{{
    "has_contradiction": true,
    "section": "{section_name}",
    "historical_stance": "Brief description of historical position",
    "current_stance": "Brief description of current position",
    "contradiction_summary": "Why this is a contradiction",
    "severity": "low|medium|high"
}}
```

If no contradiction, respond with:
```json
{{
    "has_contradiction": false
}}
```
"""


class ContradictionDetector:
    """Detect contradictions between new memos and historical investment decisions."""

    def __init__(self, db: AsyncSession, firm_id: UUID):
        self.db = db
        self.firm_id = firm_id
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.logger = logger.bind(service="contradiction_detector", firm_id=str(firm_id))
        self.vector_store = VectorStore(db, firm_id)

    async def detect_contradictions(
        self,
        memo_id: UUID,
        sections: dict,
        lookback_days: int = 730,
    ) -> list[ContradictionFlag]:
        """Detect contradictions in memo sections against historical memos."""
        self.logger.info("detecting_contradictions", memo_id=str(memo_id))

        contradictions = []

        # Sections to check for contradictions
        sections_to_check = [
            ("market_analysis", "market sizing and opportunity"),
            ("team_assessment", "team evaluation"),
            ("investment_thesis", "investment reasoning"),
            ("competitive_landscape", "competitive analysis"),
        ]

        for section_key, section_description in sections_to_check:
            section_content = sections.get(section_key)
            if not section_content:
                continue

            # Search for similar historical content
            similar_chunks = await self.vector_store.search_historical_memos(
                query=section_content,
                limit=3,
            )

            for chunk in similar_chunks:
                # Skip if similarity is too low
                if chunk["similarity"] < 0.75:
                    continue

                # Check for contradiction using Claude
                contradiction = await self._check_contradiction(
                    section_name=section_key,
                    current_content=section_content,
                    historical_title=chunk["document_title"],
                    historical_content=chunk["content"],
                    historical_memo_id=chunk["document_id"],
                )

                if contradiction:
                    contradictions.append(contradiction)

        self.logger.info(
            "contradictions_detected",
            memo_id=str(memo_id),
            count=len(contradictions),
        )
        return contradictions

    async def _check_contradiction(
        self,
        section_name: str,
        current_content: str,
        historical_title: str,
        historical_content: str,
        historical_memo_id: UUID,
    ) -> Optional[ContradictionFlag]:
        """Check if current content contradicts historical content."""
        try:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": CONTRADICTION_PROMPT.format(
                            section_name=section_name,
                            current_content=current_content[:2000],
                            historical_title=historical_title,
                            historical_content=historical_content[:2000],
                        ),
                    }
                ],
            )

            response_text = response.content[0].text

            # Parse JSON response
            import re
            import json

            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response_text)

            if result.get("has_contradiction"):
                return ContradictionFlag(
                    historical_memo_id=historical_memo_id,
                    historical_memo_title=historical_title,
                    section=result["section"],
                    historical_stance=result["historical_stance"],
                    current_stance=result["current_stance"],
                    contradiction_summary=result["contradiction_summary"],
                    severity=result.get("severity", "medium"),
                )

        except Exception as e:
            self.logger.error("contradiction_check_error", error=str(e))

        return None
