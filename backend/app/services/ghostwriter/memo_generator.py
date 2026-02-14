import time
import re
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anthropic import Anthropic
import structlog

from app.core.config import settings
from app.models.firm import Firm
from app.models.deal import Deal
from app.models.memo import InvestmentMemo, MemoTemplate, MemoStatus
from app.models.document import Document, DocumentType
from app.services.memory.vector_store import VectorStore
from app.services.ghostwriter.contradiction_detector import ContradictionDetector
from app.services.ghostwriter.ghost_loss_analyzer import GhostLossAnalyzer

logger = structlog.get_logger()


MEMO_SYSTEM_PROMPT = """You are an expert venture capital analyst at {firm_name}. Your task is to write a comprehensive Investment Committee (IC) memo for a potential investment.

FIRM IDENTITY:
- Investment Thesis: {investment_thesis}
- Focus Sectors: {focus_sectors}
- Stage Preference: {stage_preference}
- Typical Check Size: {typical_check_size}
- Historical Red Flags: {red_flags}

CRITICAL INSTRUCTION: You must be intellectually honest. Your firm has passed on deals before that went on to become massive successes. You will be provided with historical "Pass" reasons from similar deals. You MUST write a section called "Why This Might Be a Ghost Loss" that honestly confronts these patterns.

Write the memo in a professional, analytical tone. Be specific and data-driven. Flag any concerns or risks clearly. The memo should help partners make an informed investment decision.

For each section, provide substantive analysis, not just summaries. If information is missing, note what additional diligence would be needed.
"""


MEMO_GENERATION_PROMPT = """Write an Investment Committee memo for the following deal:

COMPANY: {company_name}
ONE-LINER: {one_liner}

DEAL DETAILS:
- Stage: {stage}
- Sector: {sector}
- Asking Valuation: {asking_valuation}
- Round Size: {round_size}
- Proposed Check: {proposed_check}

EXTRACTED DECK DATA:
Team Summary: {team_summary}
TAM Analysis: {tam_analysis}
Moat/Competitive Advantage: {moat_description}
Traction Metrics: {traction_metrics}

ADDITIONAL CONTEXT:
{additional_context}

---

{ghost_loss_context}

---

Write the following sections:

1. **Executive Summary** (2-3 paragraphs)
2. **Company Overview**
3. **Team Assessment**
4. **Market Analysis**
5. **Product Analysis**
6. **Business Model**
7. **Traction Analysis**
8. **Competitive Landscape**
9. **Investment Thesis** (Why we should invest)
10. **Key Risks** (What could go wrong)
11. **Deal Terms Assessment**
12. **Friction Report** (CRITICAL: For each historical pass reason above, specifically identify WHERE this deal contradicts or triggers our past logic. Use bullet points: "• [Historical pattern X]: This deal [contradicts/aligns with] because...")
13. **Why This Might Be a Ghost Loss** (Counter-thesis: What patterns from our past "passes" might we be repeating? What cognitive biases might be at play?)
14. **Why the GP Should Ignore Their Own Previous Bias Here** (CRITICAL: A specific section arguing why each historical bias (academic founders, market size, valuation) may NOT apply to this deal. Be concrete. What is different about this team, market, or terms?)
15. **Recommendation** (Proceed/Pass with reasoning - must acknowledge the Ghost Loss analysis)

Format each section with a clear header. Be direct and analytical. The Friction Report and GP bias section should challenge groupthink.
"""


class MemoGenerator:
    """Generate IC memos using LLM with firm-specific context and Ghost Loss analysis."""

    def __init__(self, db: AsyncSession, firm_id: UUID):
        self.db = db
        self.firm_id = firm_id
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.logger = logger.bind(service="memo_generator", firm_id=str(firm_id))
        self.vector_store = VectorStore(db, firm_id)
        self.contradiction_detector = ContradictionDetector(db, firm_id)
        self.ghost_loss_analyzer = GhostLossAnalyzer(db, firm_id)

    async def generate_memo(
        self,
        deal_id: UUID,
        template_id: Optional[UUID] = None,
        additional_context: Optional[str] = None,
        check_contradictions: bool = True,
        include_ghost_loss: bool = True,
    ) -> dict:
        """Generate a complete IC memo for a deal with Ghost Loss analysis."""
        start_time = time.time()
        self.logger.info("generating_memo", deal_id=str(deal_id))

        # Fetch firm and deal data
        firm = await self.db.get(Firm, self.firm_id)
        deal = await self.db.get(Deal, deal_id)

        if not deal or deal.firm_id != self.firm_id:
            raise ValueError("Deal not found or access denied")

        # Build system prompt with firm identity
        system_prompt = MEMO_SYSTEM_PROMPT.format(
            firm_name=firm.name,
            investment_thesis=firm.investment_thesis or "Not specified",
            focus_sectors=firm.focus_sectors or "Generalist",
            stage_preference=firm.stage_preference or "All stages",
            typical_check_size=firm.typical_check_size or "Not specified",
            red_flags=firm.red_flags or "None specified",
        )

        # Search for Ghost Loss patterns - historical pass reasons from similar deals
        ghost_loss_context = ""
        ghost_loss_patterns = []
        if include_ghost_loss:
            ghost_loss_patterns = await self.ghost_loss_analyzer.find_ghost_loss_patterns(
                deal=deal,
                limit=10,
            )
            ghost_loss_context = self._build_ghost_loss_context(ghost_loss_patterns)

        # Build generation prompt
        generation_prompt = MEMO_GENERATION_PROMPT.format(
            company_name=deal.company_name,
            one_liner=deal.one_liner or "Not provided",
            stage=deal.stage.value if deal.stage else "Unknown",
            sector=deal.sector or "Not specified",
            asking_valuation=f"${deal.asking_valuation:,.0f}" if deal.asking_valuation else "Not disclosed",
            round_size=f"${deal.round_size:,.0f}" if deal.round_size else "Not disclosed",
            proposed_check=f"${deal.proposed_check:,.0f}" if deal.proposed_check else "TBD",
            team_summary=deal.team_summary or "Not extracted",
            tam_analysis=deal.tam_analysis or "Not extracted",
            moat_description=deal.moat_description or "Not extracted",
            traction_metrics=str(deal.traction_metrics) if deal.traction_metrics else "Not extracted",
            additional_context=additional_context or "None provided",
            ghost_loss_context=ghost_loss_context,
        )

        # Generate memo using Claude
        response = self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=10000,
            system=system_prompt,
            messages=[{"role": "user", "content": generation_prompt}],
        )

        memo_content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        # Parse sections from generated content
        sections = self._parse_memo_sections(memo_content)

        # Create memo record
        memo = InvestmentMemo(
            deal_id=deal_id,
            firm_id=self.firm_id,
            template_id=template_id,
            title=f"IC Memo: {deal.company_name}",
            status=MemoStatus.DRAFT,
            is_ai_generated="yes",
            ai_model_used=settings.ANTHROPIC_MODEL,
            generation_prompt=generation_prompt[:5000],
            **sections,
        )

        self.db.add(memo)
        await self.db.flush()

        # Check for contradictions with historical memos
        contradictions = []
        if check_contradictions:
            contradictions = await self.contradiction_detector.detect_contradictions(
                memo_id=memo.id,
                sections=sections,
            )
            memo.contradictions = [c.dict() for c in contradictions]

        await self.db.flush()

        generation_time = time.time() - start_time
        self.logger.info(
            "memo_generated",
            memo_id=str(memo.id),
            time=generation_time,
            tokens=tokens_used,
            ghost_patterns_found=len(ghost_loss_patterns),
        )

        return {
            "memo_id": memo.id,
            "memo": memo,
            "contradictions": contradictions,
            "ghost_loss_patterns": ghost_loss_patterns,
            "generation_time_seconds": generation_time,
            "tokens_used": tokens_used,
            "model_used": settings.ANTHROPIC_MODEL,
        }

    def _build_ghost_loss_context(self, patterns: list[dict]) -> str:
        """Build the Ghost Loss context section from historical pass patterns."""
        if not patterns:
            return """GHOST LOSS ANALYSIS:
No historical pass patterns found for similar deals. This may indicate:
1. This is a genuinely novel opportunity in an underexplored space
2. Our historical data is incomplete
3. We should be especially careful about pattern-matching to avoid both false positives and false negatives

Write the Ghost Loss section focusing on common VC cognitive biases that might apply."""

        context = """⚠️ GHOST LOSS ANALYSIS - HISTORICAL PASS PATTERNS DETECTED ⚠️

The following are reasons we PASSED on similar deals in the past. Some of these companies may have gone on to succeed. Study these patterns carefully and write a counter-thesis.

HISTORICAL PASS REASONS FROM SIMILAR DEALS:
"""
        for i, pattern in enumerate(patterns, 1):
            context += f"""
--- PASS PATTERN #{i} ---
Similar Deal: {pattern.get('company_name', 'Unknown')}
Sector: {pattern.get('sector', 'Unknown')}
Pass Reason: {pattern.get('pass_reason', 'Not documented')}
Similarity Score: {pattern.get('similarity', 0):.0%}
Date: {pattern.get('pass_date', 'Unknown')}
{'-' * 40}
"""

        context += """
COGNITIVE BIASES TO CONSIDER:
1. "Too early" bias - Did we pass on a category-creator for being "too early"?
2. "Unproven team" bias - Did we underweight founder determination?
3. "Market size" bias - Did we fail to see an expanding TAM?
4. "Unit economics" bias - Did we miss that economics improve with scale?
5. "Competition" bias - Did we overweight incumbents' advantages?
6. "Consensus thinking" - Are we passing because it "doesn't feel right" vs. data?

YOUR TASK: Write a "Why This Might Be a Ghost Loss" section that HONESTLY confronts whether we might be making the same mistakes. Be uncomfortable. Be specific.
"""
        return context

    def _parse_memo_sections(self, content: str) -> dict:
        """Parse generated memo content into sections."""
        sections = {
            "executive_summary": None,
            "company_overview": None,
            "team_assessment": None,
            "market_analysis": None,
            "product_analysis": None,
            "business_model": None,
            "traction_analysis": None,
            "competitive_landscape": None,
            "investment_thesis": None,
            "key_risks": None,
            "deal_terms": None,
            "friction_report": None,
            "ghost_loss_analysis": None,
            "gp_bias_ignore_reasoning": None,
            "recommendation": None,
        }

        section_patterns = {
            "executive_summary": ["Executive Summary", "Summary"],
            "company_overview": ["Company Overview", "Overview"],
            "team_assessment": ["Team Assessment", "Team"],
            "market_analysis": ["Market Analysis", "Market"],
            "product_analysis": ["Product Analysis", "Product"],
            "business_model": ["Business Model"],
            "traction_analysis": ["Traction Analysis", "Traction"],
            "competitive_landscape": ["Competitive Landscape", "Competition"],
            "investment_thesis": ["Investment Thesis"],
            "key_risks": ["Key Risks", "Risks"],
            "deal_terms": ["Deal Terms", "Terms Assessment"],
            "friction_report": ["Friction Report"],
            "ghost_loss_analysis": ["Why This Might Be a Ghost Loss", "Ghost Loss", "Counter-Thesis"],
            "gp_bias_ignore_reasoning": ["Why the GP Should Ignore", "GP Should Ignore", "Previous Bias"],
            "recommendation": ["Recommendation"],
        }

        # Split by section headers
        current_section = None
        current_content = []

        lines = content.split("\n")
        for line in lines:
            # Check if this line is a section header
            header_match = None
            for section_key, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.match(rf"^\*?\*?#{0,3}\s*\d*\.?\s*{re.escape(pattern)}\s*\*?\*?$", line.strip(), re.IGNORECASE):
                        header_match = section_key
                        break
                if header_match:
                    break

            if header_match:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = header_match
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        # If parsing failed, put everything in executive summary
        if not any(sections.values()):
            sections["executive_summary"] = content

        return sections
