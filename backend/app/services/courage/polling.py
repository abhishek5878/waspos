from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import structlog

from app.models.polling import ConvictionPoll, PollVote
from app.models.deal import Deal
from app.schemas.polling import ConvictionPollCreate, PollVoteCreate, PollVoteResponse

logger = structlog.get_logger()


class PollingService:
    """Service for managing blind IC polling."""

    def __init__(self, db: AsyncSession, firm_id: UUID):
        self.db = db
        self.firm_id = firm_id
        self.logger = logger.bind(service="polling", firm_id=str(firm_id))

    async def create_poll(
        self,
        data: ConvictionPollCreate,
        created_by: UUID,
    ) -> ConvictionPoll:
        """Create a new conviction poll for a deal."""
        # Verify deal belongs to firm
        deal = await self.db.get(Deal, data.deal_id)
        if not deal or deal.firm_id != self.firm_id:
            raise ValueError("Deal not found or access denied")

        poll = ConvictionPoll(
            deal_id=data.deal_id,
            firm_id=self.firm_id,
            title=data.title,
            description=data.description,
            closes_at=data.closes_at,
            ic_meeting_date=data.ic_meeting_date,
            reveal_threshold=data.reveal_threshold,
        )

        self.db.add(poll)
        await self.db.flush()

        self.logger.info("poll_created", poll_id=str(poll.id), deal_id=str(data.deal_id))
        return poll

    async def submit_vote(
        self,
        poll_id: UUID,
        user_id: UUID,
        data: PollVoteCreate,
    ) -> PollVote:
        """Submit a vote to a poll."""
        poll = await self.db.get(ConvictionPoll, poll_id)
        if not poll or poll.firm_id != self.firm_id:
            raise ValueError("Poll not found or access denied")

        if not poll.is_active:
            raise ValueError("Poll is no longer active")

        if poll.closes_at and datetime.utcnow() > poll.closes_at:
            raise ValueError("Poll has closed")

        # Check if user already voted
        existing = await self.db.execute(
            select(PollVote).where(
                PollVote.poll_id == poll_id,
                PollVote.user_id == user_id,
            )
        )
        existing_vote = existing.scalar_one_or_none()

        if existing_vote:
            # Update existing vote
            existing_vote.conviction_score = data.conviction_score
            existing_vote.red_flags = data.red_flags
            existing_vote.red_flag_notes = data.red_flag_notes
            existing_vote.green_flags = data.green_flags
            existing_vote.green_flag_notes = data.green_flag_notes
            existing_vote.private_notes = data.private_notes
            existing_vote.updated_at = datetime.utcnow()
            vote = existing_vote
            self.logger.info("vote_updated", poll_id=str(poll_id), user_id=str(user_id))
        else:
            # Create new vote
            vote = PollVote(
                poll_id=poll_id,
                user_id=user_id,
                conviction_score=data.conviction_score,
                red_flags=data.red_flags,
                red_flag_notes=data.red_flag_notes,
                green_flags=data.green_flags,
                green_flag_notes=data.green_flag_notes,
                private_notes=data.private_notes,
            )
            self.db.add(vote)
            self.logger.info("vote_submitted", poll_id=str(poll_id), user_id=str(user_id))

        await self.db.flush()

        # Check if we should auto-reveal
        await self._check_reveal_threshold(poll)

        return vote

    async def _check_reveal_threshold(self, poll: ConvictionPoll):
        """Check if poll should be revealed based on vote count."""
        vote_count = await self.db.execute(
            select(func.count(PollVote.id)).where(PollVote.poll_id == poll.id)
        )
        count = vote_count.scalar()

        if count >= poll.reveal_threshold and not poll.is_revealed:
            # Could auto-reveal here, but leaving manual for now
            pass

    async def reveal_poll(self, poll_id: UUID, revealed_by: UUID) -> ConvictionPoll:
        """Reveal poll results to all participants."""
        poll = await self.db.get(ConvictionPoll, poll_id)
        if not poll or poll.firm_id != self.firm_id:
            raise ValueError("Poll not found or access denied")

        poll.is_revealed = True
        poll.is_active = False

        # Calculate final scores
        result = await self.db.execute(
            select(PollVote).where(PollVote.poll_id == poll_id)
        )
        votes = result.scalars().all()

        if votes:
            scores = [v.conviction_score for v in votes]
            poll.average_score = sum(scores) // len(scores)
            poll.divergence_score = max(scores) - min(scores)

        await self.db.flush()
        self.logger.info("poll_revealed", poll_id=str(poll_id))
        return poll

    async def get_poll_votes(
        self,
        poll_id: UUID,
        requester_id: UUID,
        include_identities: bool = False,
    ) -> list[PollVoteResponse]:
        """Get votes for a poll (respecting blind status)."""
        poll = await self.db.get(ConvictionPoll, poll_id)
        if not poll or poll.firm_id != self.firm_id:
            raise ValueError("Poll not found or access denied")

        result = await self.db.execute(
            select(PollVote)
            .options(selectinload(PollVote.user))
            .where(PollVote.poll_id == poll_id)
        )
        votes = result.scalars().all()

        responses = []
        for vote in votes:
            response = PollVoteResponse(
                id=vote.id,
                poll_id=vote.poll_id,
                conviction_score=vote.conviction_score,
                red_flags=vote.red_flags,
                green_flags=vote.green_flags,
                submitted_at=vote.submitted_at,
            )

            # Include identity info only if revealed or requester is the voter
            if poll.is_revealed or vote.user_id == requester_id:
                response.user_id = vote.user_id
                response.user_name = vote.user.full_name if vote.user else None
                response.red_flag_notes = vote.red_flag_notes
                response.green_flag_notes = vote.green_flag_notes

            responses.append(response)

        return responses

    async def get_user_vote(self, poll_id: UUID, user_id: UUID) -> Optional[PollVote]:
        """Get a user's vote for a specific poll."""
        result = await self.db.execute(
            select(PollVote).where(
                PollVote.poll_id == poll_id,
                PollVote.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
