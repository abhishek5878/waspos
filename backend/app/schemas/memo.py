from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.memo import MemoStatus


class ContradictionFlag(BaseModel):
    """A contradiction with historical memo."""
    historical_memo_id: UUID
    historical_memo_title: str
    section: str
    historical_stance: str
    current_stance: str
    contradiction_summary: str
    severity: str = Field(default="medium")  # low, medium, high


class GhostLossPattern(BaseModel):
    """A historical pass pattern that might indicate a Ghost Loss."""
    type: str  # "passed_deal" or "historical_memo"
    company_name: Optional[str] = None
    sector: Optional[str] = None
    pass_reason: Optional[str] = None
    pass_date: Optional[str] = None
    similarity: float
    one_liner: Optional[str] = None
    source_content: Optional[str] = None


class InvestmentMemoBase(BaseModel):
    """Base investment memo schema."""
    title: str = Field(..., min_length=1, max_length=255)


class InvestmentMemoCreate(InvestmentMemoBase):
    """Schema for creating a memo."""
    deal_id: UUID
    template_id: Optional[UUID] = None


class InvestmentMemoUpdate(BaseModel):
    """Schema for updating a memo."""
    title: Optional[str] = None
    status: Optional[MemoStatus] = None
    executive_summary: Optional[str] = None
    company_overview: Optional[str] = None
    team_assessment: Optional[str] = None
    market_analysis: Optional[str] = None
    product_analysis: Optional[str] = None
    business_model: Optional[str] = None
    traction_analysis: Optional[str] = None
    competitive_landscape: Optional[str] = None
    investment_thesis: Optional[str] = None
    key_risks: Optional[str] = None
    deal_terms: Optional[str] = None
    ghost_loss_analysis: Optional[str] = None
    recommendation: Optional[str] = None


class InvestmentMemoResponse(BaseModel):
    """Full investment memo response."""
    id: UUID
    deal_id: UUID
    firm_id: UUID
    author_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    title: str
    status: MemoStatus

    # Content sections
    executive_summary: Optional[str] = None
    company_overview: Optional[str] = None
    team_assessment: Optional[str] = None
    market_analysis: Optional[str] = None
    product_analysis: Optional[str] = None
    business_model: Optional[str] = None
    traction_analysis: Optional[str] = None
    competitive_landscape: Optional[str] = None
    investment_thesis: Optional[str] = None
    key_risks: Optional[str] = None
    deal_terms: Optional[str] = None
    friction_report: Optional[str] = None
    ghost_loss_analysis: Optional[str] = None  # "Why This Might Be a Ghost Loss"
    gp_bias_ignore_reasoning: Optional[str] = None  # "Why the GP should ignore previous bias"
    recommendation: Optional[str] = None

    # AI metadata
    is_ai_generated: str
    ai_model_used: Optional[str] = None
    contradictions: Optional[list[dict]] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GhostwriterRequest(BaseModel):
    """Request to generate an IC memo using Ghostwriter."""
    deal_id: UUID
    template_id: Optional[UUID] = None

    # Optional overrides
    deck_document_id: Optional[UUID] = None
    additional_context: Optional[str] = None
    tone: Optional[str] = Field(None, description="e.g., 'bullish', 'skeptical', 'neutral'")
    focus_areas: Optional[list[str]] = Field(None, description="Sections to emphasize")

    # Ghost Loss settings
    include_ghost_loss: bool = Field(default=True, description="Include Ghost Loss counter-thesis analysis")

    # Historical comparison settings
    check_contradictions: bool = Field(default=True)
    historical_lookback_days: int = Field(default=1095)  # 3 years


class GhostwriterResponse(BaseModel):
    """Response from Ghostwriter memo generation."""
    memo_id: UUID
    memo: InvestmentMemoResponse
    contradictions: list[ContradictionFlag] = []
    ghost_loss_patterns: list[GhostLossPattern] = []  # Historical pass patterns found
    historical_memos_analyzed: int
    generation_time_seconds: float
    tokens_used: int
    model_used: str
