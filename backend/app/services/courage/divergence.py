from typing import Optional
from uuid import UUID
from collections import Counter
import statistics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.models.polling import ConvictionPoll, PollVote
from app.models.deal import Deal
from app.schemas.polling import DivergenceView, PollVoteResponse

logger = structlog.get_logger()


class DivergenceAnalyzer:
    """Analyze voting divergence for lead partner insights."""

    def __init__(self, db: AsyncSession, firm_id: UUID):
        self.db = db
        self.firm_id = firm_id
        self.logger = logger.bind(service="divergence", firm_id=str(firm_id))

    async def get_divergence_view(
        self,
        poll_id: UUID,
        requester_id: UUID,
        is_lead_partner: bool = False,
    ) -> DivergenceView:
        """Get divergence analysis for a poll."""
        # Fetch poll with deal info
        result = await self.db.execute(
            select(ConvictionPoll)
            .options(selectinload(ConvictionPoll.deal))
            .where(
                ConvictionPoll.id == poll_id,
                ConvictionPoll.firm_id == self.firm_id,
            )
        )
        poll = result.scalar_one_or_none()

        if not poll:
            raise ValueError("Poll not found or access denied")

        # Fetch all votes
        votes_result = await self.db.execute(
            select(PollVote)
            .options(selectinload(PollVote.user))
            .where(PollVote.poll_id == poll_id)
        )
        votes = votes_result.scalars().all()

        if not votes:
            raise ValueError("No votes submitted yet")

        # Calculate statistics
        scores = [v.conviction_score for v in votes]
        min_score = min(scores)
        max_score = max(scores)
        divergence = max_score - min_score
        avg_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0

        # Score distribution
        distribution = {i: 0 for i in range(1, 11)}
        for score in scores:
            distribution[score] += 1

        # Aggregate red flags
        all_red_flags = []
        all_green_flags = []
        for vote in votes:
            if vote.red_flags:
                all_red_flags.extend(vote.red_flags)
            if vote.green_flags:
                all_green_flags.extend(vote.green_flags)

        red_flag_counts = Counter(all_red_flags)
        green_flag_counts = Counter(all_green_flags)

        top_red_flags = [
            {"flag": flag, "count": count}
            for flag, count in red_flag_counts.most_common(5)
        ]
        top_green_flags = [
            {"flag": flag, "count": count}
            for flag, count in green_flag_counts.most_common(5)
        ]

        # Build vote responses (only if revealed or lead partner)
        vote_responses = None
        if poll.is_revealed or is_lead_partner:
            vote_responses = [
                PollVoteResponse(
                    id=v.id,
                    poll_id=v.poll_id,
                    conviction_score=v.conviction_score,
                    red_flags=v.red_flags,
                    green_flags=v.green_flags,
                    submitted_at=v.submitted_at,
                    user_id=v.user_id if poll.is_revealed else None,
                    user_name=v.user.full_name if poll.is_revealed and v.user else None,
                    red_flag_notes=v.red_flag_notes if poll.is_revealed else None,
                    green_flag_notes=v.green_flag_notes if poll.is_revealed else None,
                )
                for v in votes
            ]

        return DivergenceView(
            poll_id=poll.id,
            deal_id=poll.deal_id,
            company_name=poll.deal.company_name,
            total_votes=len(votes),
            average_score=round(avg_score, 2),
            min_score=min_score,
            max_score=max_score,
            divergence=divergence,
            std_deviation=round(std_dev, 2),
            score_distribution=distribution,
            top_red_flags=top_red_flags,
            top_green_flags=top_green_flags,
            has_consensus=divergence <= 2,
            needs_discussion=divergence >= 5,
            votes=vote_responses,
        )

    async def get_high_divergence_deals(
        self,
        min_divergence: int = 4,
        limit: int = 10,
    ) -> list[dict]:
        """Get deals with high voting divergence for IC attention."""
        result = await self.db.execute(
            select(ConvictionPoll)
            .options(selectinload(ConvictionPoll.deal))
            .where(
                ConvictionPoll.firm_id == self.firm_id,
                ConvictionPoll.divergence_score >= min_divergence,
                ConvictionPoll.is_active == True,
            )
            .order_by(ConvictionPoll.divergence_score.desc())
            .limit(limit)
        )
        polls = result.scalars().all()

        return [
            {
                "poll_id": poll.id,
                "deal_id": poll.deal_id,
                "company_name": poll.deal.company_name,
                "divergence": poll.divergence_score,
                "average_score": poll.average_score,
                "ic_meeting_date": poll.ic_meeting_date,
            }
            for poll in polls
        ]
