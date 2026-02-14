from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.polling import ConvictionPoll
from app.models.deal import Deal
from app.schemas.polling import (
    ConvictionPollCreate,
    ConvictionPollResponse,
    PollVoteCreate,
    PollVoteResponse,
    DivergenceView,
)
from app.services.courage.polling import PollingService
from app.services.courage.divergence import DivergenceAnalyzer

router = APIRouter(prefix="/polls", tags=["polling"])


@router.post("/", response_model=ConvictionPollResponse, status_code=201)
async def create_poll(
    data: ConvictionPollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new conviction poll for a deal."""
    firm_id = current_user["firm_id"]
    user_id = current_user["user_id"]

    service = PollingService(db, firm_id)

    try:
        poll = await service.create_poll(data, user_id)
        return ConvictionPollResponse(
            id=poll.id,
            deal_id=poll.deal_id,
            firm_id=poll.firm_id,
            title=poll.title,
            description=poll.description,
            is_active=poll.is_active,
            is_revealed=poll.is_revealed,
            reveal_threshold=poll.reveal_threshold,
            opens_at=poll.opens_at,
            closes_at=poll.closes_at,
            ic_meeting_date=poll.ic_meeting_date,
            created_at=poll.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{poll_id}", response_model=ConvictionPollResponse)
async def get_poll(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get poll details."""
    poll = await db.get(ConvictionPoll, poll_id)
    if not poll or poll.firm_id != current_user["firm_id"]:
        raise HTTPException(status_code=404, detail="Poll not found")

    return ConvictionPollResponse(
        id=poll.id,
        deal_id=poll.deal_id,
        firm_id=poll.firm_id,
        title=poll.title,
        description=poll.description,
        is_active=poll.is_active,
        is_revealed=poll.is_revealed,
        reveal_threshold=poll.reveal_threshold,
        opens_at=poll.opens_at,
        closes_at=poll.closes_at,
        ic_meeting_date=poll.ic_meeting_date,
        created_at=poll.created_at,
        average_score=poll.average_score if poll.is_revealed else None,
        divergence_score=poll.divergence_score if poll.is_revealed else None,
    )


@router.post("/{poll_id}/vote", response_model=PollVoteResponse)
async def submit_vote(
    poll_id: UUID,
    data: PollVoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a conviction vote."""
    firm_id = current_user["firm_id"]
    user_id = current_user["user_id"]

    service = PollingService(db, firm_id)

    try:
        vote = await service.submit_vote(poll_id, user_id, data)
        return PollVoteResponse(
            id=vote.id,
            poll_id=vote.poll_id,
            conviction_score=vote.conviction_score,
            red_flags=vote.red_flags,
            green_flags=vote.green_flags,
            submitted_at=vote.submitted_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{poll_id}/my-vote", response_model=Optional[PollVoteResponse])
async def get_my_vote(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current user's vote for a poll."""
    firm_id = current_user["firm_id"]
    user_id = current_user["user_id"]

    service = PollingService(db, firm_id)
    vote = await service.get_user_vote(poll_id, user_id)

    if not vote:
        return None

    return PollVoteResponse(
        id=vote.id,
        poll_id=vote.poll_id,
        conviction_score=vote.conviction_score,
        red_flags=vote.red_flags,
        green_flags=vote.green_flags,
        submitted_at=vote.submitted_at,
        user_id=user_id,
        red_flag_notes=vote.red_flag_notes,
        green_flag_notes=vote.green_flag_notes,
    )


@router.post("/{poll_id}/reveal", response_model=ConvictionPollResponse)
async def reveal_poll(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reveal poll results (lead partner only)."""
    firm_id = current_user["firm_id"]
    user_id = current_user["user_id"]

    # TODO: Add lead partner check

    service = PollingService(db, firm_id)

    try:
        poll = await service.reveal_poll(poll_id, user_id)
        return ConvictionPollResponse(
            id=poll.id,
            deal_id=poll.deal_id,
            firm_id=poll.firm_id,
            title=poll.title,
            description=poll.description,
            is_active=poll.is_active,
            is_revealed=poll.is_revealed,
            reveal_threshold=poll.reveal_threshold,
            opens_at=poll.opens_at,
            closes_at=poll.closes_at,
            ic_meeting_date=poll.ic_meeting_date,
            created_at=poll.created_at,
            average_score=poll.average_score,
            divergence_score=poll.divergence_score,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{poll_id}/divergence", response_model=DivergenceView)
async def get_divergence_view(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get divergence analysis (lead partner view)."""
    firm_id = current_user["firm_id"]
    user_id = current_user["user_id"]

    # TODO: Check if user is lead partner for this deal
    is_lead_partner = True  # Placeholder

    analyzer = DivergenceAnalyzer(db, firm_id)

    try:
        return await analyzer.get_divergence_view(poll_id, user_id, is_lead_partner)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deal/{deal_id}")
async def get_deal_polls(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all polls for a deal."""
    result = await db.execute(
        select(ConvictionPoll)
        .where(
            ConvictionPoll.deal_id == deal_id,
            ConvictionPoll.firm_id == current_user["firm_id"],
        )
        .order_by(ConvictionPoll.created_at.desc())
    )
    polls = result.scalars().all()

    return {
        "polls": [
            ConvictionPollResponse(
                id=p.id,
                deal_id=p.deal_id,
                firm_id=p.firm_id,
                title=p.title,
                description=p.description,
                is_active=p.is_active,
                is_revealed=p.is_revealed,
                reveal_threshold=p.reveal_threshold,
                opens_at=p.opens_at,
                closes_at=p.closes_at,
                ic_meeting_date=p.ic_meeting_date,
                created_at=p.created_at,
                average_score=p.average_score if p.is_revealed else None,
                divergence_score=p.divergence_score if p.is_revealed else None,
            )
            for p in polls
        ]
    }
