import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class MemoStatus(str, Enum):
    """Investment memo status."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    FINAL = "final"
    ARCHIVED = "archived"


class InvestmentMemo(Base):
    """Investment Committee memo for a deal."""

    __tablename__ = "investment_memos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("memo_templates.id"), nullable=True)

    # Memo Content
    title = Column(String(255), nullable=False)
    status = Column(SQLEnum(MemoStatus), default=MemoStatus.DRAFT)

    # Structured sections (Ghostwriter output)
    executive_summary = Column(Text, nullable=True)
    company_overview = Column(Text, nullable=True)
    team_assessment = Column(Text, nullable=True)
    market_analysis = Column(Text, nullable=True)
    product_analysis = Column(Text, nullable=True)
    business_model = Column(Text, nullable=True)
    traction_analysis = Column(Text, nullable=True)
    competitive_landscape = Column(Text, nullable=True)
    investment_thesis = Column(Text, nullable=True)
    key_risks = Column(Text, nullable=True)
    deal_terms = Column(Text, nullable=True)
    friction_report = Column(Text, nullable=True)  # Where deal contradicts past logic
    ghost_loss_analysis = Column(Text, nullable=True)  # "Why This Might Be a Ghost Loss"
    gp_bias_ignore_reasoning = Column(Text, nullable=True)  # "Why the GP should ignore previous bias"
    recommendation = Column(Text, nullable=True)

    # Ghostwriter Metadata
    is_ai_generated = Column(String(10), default="no")  # "yes", "no", "assisted"
    ai_model_used = Column(String(100), nullable=True)
    generation_prompt = Column(Text, nullable=True)

    # Historical Contradiction Flags
    contradictions = Column(JSONB, nullable=True)
    # [{"historical_memo_id": "...", "section": "market", "contradiction": "..."}]

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal = relationship("Deal", back_populates="memos")
    author = relationship("User", back_populates="authored_memos")
    template = relationship("MemoTemplate", back_populates="memos")

    def __repr__(self):
        return f"<InvestmentMemo {self.title}>"


class MemoTemplate(Base):
    """Firm-specific memo template."""

    __tablename__ = "memo_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(String(10), default="no")

    # Template structure
    sections = Column(JSONB, nullable=False)
    # [{"name": "Executive Summary", "prompt": "...", "required": true}]

    # Firm-specific prompts
    tone_guidance = Column(Text, nullable=True)
    evaluation_criteria = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="memo_templates")
    memos = relationship("InvestmentMemo", back_populates="template")

    def __repr__(self):
        return f"<MemoTemplate {self.name}>"
