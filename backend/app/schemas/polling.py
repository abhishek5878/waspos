from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class PollVoteCreate(BaseModel):
    """Schema for submitting a conviction vote."""
    conviction_score: int = Field(..., ge=1, le=10)
    red_flags: Optional[list[str]] = None
    red_flag_notes: Optional[str] = None
    green_flags: Optional[list[str]] = None
    green_flag_notes: Optional[str] = None
    private_notes: Optional[str] = None

    @field_validator("conviction_score")
    @classmethod
    def validate_score(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Conviction score must be between 1 and 10")
        return v


class PollVoteResponse(BaseModel):
    """Response for a poll vote (hidden identity before reveal)."""
    id: UUID
    poll_id: UUID
    conviction_score: int
    red_flags: Optional[list[str]] = None
    green_flags: Optional[list[str]] = None
    submitted_at: datetime

    # Only included after reveal
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    red_flag_notes: Optional[str] = None
    green_flag_notes: Optional[str] = None

    class Config:
        from_attributes = True


class ConvictionPollCreate(BaseModel):
    """Schema for creating a conviction poll."""
    deal_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    closes_at: Optional[datetime] = None
    ic_meeting_date: Optional[datetime] = None
    reveal_threshold: int = Field(default=3, ge=1)


class ConvictionPollResponse(BaseModel):
    """Response for a conviction poll."""
    id: UUID
    deal_id: UUID
    firm_id: UUID
    title: str
    description: Optional[str] = None
    is_active: bool
    is_revealed: bool
    reveal_threshold: int
    opens_at: datetime
    closes_at: Optional[datetime] = None
    ic_meeting_date: Optional[datetime] = None
    vote_count: int = 0
    company_name: Optional[str] = None
    created_at: datetime

    # Only populated if is_revealed or requester is lead partner
    average_score: Optional[float] = None
    divergence_score: Optional[int] = None

    class Config:
        from_attributes = True


class DivergenceView(BaseModel):
    """Divergence analysis for lead partner view."""
    poll_id: UUID
    deal_id: UUID
    company_name: str

    # Aggregated scores
    total_votes: int
    average_score: float
    min_score: int
    max_score: int
    divergence: int  # max - min
    std_deviation: float

    # Score distribution
    score_distribution: dict[int, int]  # {1: 0, 2: 1, 3: 0, ...}

    # Aggregated flags (anonymous)
    top_red_flags: list[dict]  # [{"flag": "market timing", "count": 3}]
    top_green_flags: list[dict]

    # Consensus indicators
    has_consensus: bool = Field(description="True if divergence <= 2")
    needs_discussion: bool = Field(description="True if divergence >= 5")

    # Individual votes (only if revealed)
    votes: Optional[list[PollVoteResponse]] = None


class VoteSummary(BaseModel):
    """Anonymous summary of a single vote for blind viewing."""
    conviction_score: int
    red_flag_count: int
    green_flag_count: int
    has_notes: bool
