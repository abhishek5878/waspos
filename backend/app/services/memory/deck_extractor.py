import re
from typing import Optional
import structlog
from anthropic import Anthropic

from app.core.config import settings
from app.services.memory.pdf_parser import PDFParser

logger = structlog.get_logger()


EXTRACTION_PROMPT = """You are an expert VC analyst. Extract key information from this pitch deck.

Analyze the following pitch deck content and extract:

1. **Company Name**: The name of the company
2. **One-Liner**: A single sentence describing what the company does
3. **Team Summary**: Key team members, their backgrounds, and relevant experience (2-3 sentences)
4. **TAM Analysis**: Total Addressable Market size and how they calculated it
5. **Moat/Competitive Advantage**: What makes this company defensible
6. **Traction Metrics**: Current metrics (MRR, ARR, customers, growth rate, etc.)
7. **Ask**: How much they're raising and at what valuation

Respond in JSON format:
```json
{
    "company_name": "string",
    "one_liner": "string",
    "team_summary": "string",
    "tam_analysis": "string",
    "moat_description": "string",
    "traction_metrics": {
        "mrr": number or null,
        "arr": number or null,
        "customers": number or null,
        "growth_rate": number or null,
        "other_metrics": {}
    },
    "funding_stage": "string",
    "ask_amount": "string",
    "founded_year": number or null,
    "location": "string or null",
    "sections_found": ["list of sections identified in deck"]
}
```

PITCH DECK CONTENT:
{deck_content}
"""


class DeckExtractor:
    """Extract structured data from pitch decks using LLM."""

    def __init__(self):
        self.logger = logger.bind(service="deck_extractor")
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.pdf_parser = PDFParser()

    async def extract_from_pdf(self, pdf_bytes: bytes, filename: str) -> dict:
        """Extract key data from a pitch deck PDF."""
        self.logger.info("extracting_deck_data", filename=filename)

        # Parse the PDF
        parsed = await self.pdf_parser.parse_bytes(pdf_bytes, filename)
        deck_content = parsed["full_text"]

        # Truncate if too long (Claude context limit)
        if len(deck_content) > 100000:
            deck_content = deck_content[:100000] + "\n\n[Content truncated...]"

        # Extract using Claude
        try:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": EXTRACTION_PROMPT.format(deck_content=deck_content),
                    }
                ],
            )

            # Parse the JSON response
            response_text = response.content[0].text
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)

            if json_match:
                import json
                extracted = json.loads(json_match.group(1))
            else:
                # Try to parse the whole response as JSON
                import json
                extracted = json.loads(response_text)

            extracted["page_count"] = parsed["metadata"].get("page_count", 0)
            extracted["extraction_confidence"] = 0.85  # Placeholder

            self.logger.info("deck_extraction_complete", company=extracted.get("company_name"))
            return extracted

        except Exception as e:
            self.logger.error("deck_extraction_error", error=str(e))
            return {
                "company_name": None,
                "one_liner": None,
                "team_summary": None,
                "tam_analysis": None,
                "moat_description": None,
                "traction_metrics": None,
                "page_count": parsed["metadata"].get("page_count", 0),
                "extraction_confidence": 0.0,
                "sections_found": [],
                "error": str(e),
            }

    async def extract_from_file(self, file_path: str) -> dict:
        """Extract key data from a pitch deck file."""
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        return await self.extract_from_pdf(pdf_bytes, file_path)
