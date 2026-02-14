import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class ConvictionPoll(Base):
    """Blind IC polling session for a deal."""

    __tablename__ = "conviction_polls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)

    # Poll Configuration
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_revealed = Column(Boolean, default=False)  # Votes visible to all
    reveal_threshold = Column(Integer, default=0)  # Min votes before reveal

    # Timestamps
    opens_at = Column(DateTime, default=datetime.utcnow)
    closes_at = Column(DateTime, nullable=True)
    ic_meeting_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Computed after reveal
    divergence_score = Column(Integer, nullable=True)  # Max score - Min score
    average_score = Column(Integer, nullable=True)

    # Relationships
    deal = relationship("Deal", back_populates="polls")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ConvictionPoll {self.title}>"

    def calculate_divergence(self):
        """Calculate divergence between highest and lowest scores."""
        if not self.votes:
            return None
        scores = [v.conviction_score for v in self.votes if v.conviction_score is not None]
        if len(scores) < 2:
            return None
        return max(scores) - min(scores)


class PollVote(Base):
    """Individual vote in a conviction poll."""

    __tablename__ = "poll_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("conviction_polls.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Conviction Score (1-10)
    conviction_score = Column(Integer, nullable=False)

    # Red Flags (anonymous concerns)
    red_flags = Column(JSONB, nullable=True)  # ["market timing", "team risk"]
    red_flag_notes = Column(Text, nullable=True)

    # Positive Signals
    green_flags = Column(JSONB, nullable=True)
    green_flag_notes = Column(Text, nullable=True)

    # Overall thoughts
    private_notes = Column(Text, nullable=True)  # Only visible to voter

    # Meta
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    poll = relationship("ConvictionPoll", back_populates="votes")
    user = relationship("User", back_populates="poll_votes")

    def __repr__(self):
        return f"<PollVote score={self.conviction_score}>"
