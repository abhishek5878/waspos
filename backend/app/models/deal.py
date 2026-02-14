import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class DealStage(str, Enum):
    """Deal pipeline stages."""
    INBOUND = "inbound"
    SCREENING = "screening"
    FIRST_MEETING = "first_meeting"
    DEEP_DIVE = "deep_dive"
    IC_REVIEW = "ic_review"
    TERM_SHEET = "term_sheet"
    DUE_DILIGENCE = "due_diligence"
    CLOSED = "closed"
    PASSED = "passed"


class DealSource(str, Enum):
    """How the deal was sourced."""
    INBOUND = "inbound"
    REFERRAL = "referral"
    PORTFOLIO_INTRO = "portfolio_intro"
    OUTBOUND = "outbound"
    CONFERENCE = "conference"
    OTHER = "other"


class Deal(Base):
    """Deal/Company entity - the core unit of pipeline tracking."""

    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)
    lead_partner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Company Info
    company_name = Column(String(255), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    one_liner = Column(String(500), nullable=True)

    # Extracted Deck Data
    team_summary = Column(Text, nullable=True)
    tam_analysis = Column(Text, nullable=True)
    moat_description = Column(Text, nullable=True)
    traction_metrics = Column(JSONB, nullable=True)  # {"mrr": 100000, "growth_rate": 0.15}

    # Deal Details
    stage = Column(SQLEnum(DealStage), default=DealStage.INBOUND, index=True)
    source = Column(SQLEnum(DealSource), default=DealSource.INBOUND)
    sector = Column(String(100), nullable=True, index=True)
    sub_sector = Column(String(100), nullable=True)

    # Financials
    asking_valuation = Column(Numeric(15, 2), nullable=True)
    proposed_check = Column(Numeric(15, 2), nullable=True)
    round_size = Column(Numeric(15, 2), nullable=True)

    # Metadata
    referrer = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    pass_reason = Column(Text, nullable=True)  # Why we passed

    # Timestamps
    first_contact_date = Column(DateTime, nullable=True)
    ic_date = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="deals")
    lead_partner = relationship("User", back_populates="led_deals", foreign_keys=[lead_partner_id])
    documents = relationship("Document", back_populates="deal", cascade="all, delete-orphan")
    memos = relationship("InvestmentMemo", back_populates="deal", cascade="all, delete-orphan")
    polls = relationship("ConvictionPoll", back_populates="deal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Deal {self.company_name}>"
