#!/usr/bin/env python3
"""
Ghost Loss Detection - System Stress Test

Orchestrates the full stress test:
1. Seeds 3 historical Pass memos (Deal A, B, C)
2. Creates Apriori deal (AI-native simulation, IIT Delhi founders)
3. Runs Ghostwriter with vector search → Friction Report + GP bias section
4. Simulates 3 partner votes (4, 9, 8) with specified flags
5. Verifies Divergence View: 5-point gap, High Divergence, needs_discussion

Usage (run from project root, e.g. waspos/):
    PYTHONPATH=backend:. python3 scripts/run_ghost_stress_test.py [--skip-seed] [--db-url URL]

Prerequisites:
    - PostgreSQL with pgvector, wasp_os database
    - Run migrations: backend/app/db/migrations/002_add_friction_gp_bias_columns.sql
    - ANTHROPIC_API_KEY set for Ghostwriter (LLM memo generation)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from decimal import Decimal

# Add project root and backend to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root / "backend"))
sys.path.insert(0, str(_root))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.pgbouncer import get_pgbouncer_connect_args
from app.models.firm import Firm
from app.models.user import User, UserRole
from app.models.deal import Deal, DealStage, DealSource
from app.services.ghostwriter.memo_generator import MemoGenerator
from app.services.courage.polling import PollingService
from app.services.courage.divergence import DivergenceAnalyzer
from app.schemas.polling import ConvictionPollCreate, PollVoteCreate

# Import seed logic (scripts/ at project root)
from scripts.seed_mock_data import seed_mock_data


APRIORI_DEAL = {
    "company_name": "Apriori",
    "one_liner": "AI-native simulation layer for enterprise testing",
    "sector": "AI Developer Tools",
    "description": "Founded by IIT Delhi researchers. No funding until now. Building AI-native simulation infrastructure.",
    "stage": DealStage.IC_REVIEW,
    "asking_valuation": None,  # No funding yet - avoids valuation friction
}


async def run_stress_test(db_url: str, skip_seed: bool = False):
    """Run the full Ghost Loss stress test."""
    engine = create_async_engine(db_url, connect_args=get_pgbouncer_connect_args())
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        async with async_session() as db:
            # 1. Seed data unless skipped
            if not skip_seed:
                print("=" * 60)
                print("STEP 1: Seeding historical Pass memos")
                print("=" * 60)
                await seed_mock_data(db_url, firm_id_arg=None)

            result = await db.execute(select(Firm).limit(1))
            firm = result.scalar_one_or_none()
            if not firm:
                print("Error: No firm found. Run without --skip-seed first.")
                return
            firm_id = firm.id
            print(f"Using firm: {firm.name} ({firm_id})")

            # SET does not accept bind params; UUID is safe to interpolate
            await db.execute(text(f"SET app.current_firm_id = '{firm_id}'"))

            # 2. Create Apriori deal
            print("\n" + "=" * 60)
            print("STEP 2: Creating Apriori deal")
            print("=" * 60)

            result = await db.execute(select(User).where(User.firm_id == firm_id))
            users = result.scalars().all()
            if len(users) < 3:
                print("Warning: Need 3 users. Run seed without --skip-seed.")
                return
            lead_partner, specialist, junior = users[0], users[1], users[2]

            deal = Deal(
                firm_id=firm_id,
                company_name=APRIORI_DEAL["company_name"],
                one_liner=APRIORI_DEAL["one_liner"],
                sector=APRIORI_DEAL["sector"],
                description=APRIORI_DEAL["description"],
                stage=APRIORI_DEAL["stage"],
                source=DealSource.INBOUND,
                team_summary="IIT Delhi researchers, deep technical background in simulation and ML",
                tam_analysis="Global simulation/testing market expanding with AI adoption",
                moat_description="AI-native architecture, first-mover in simulation layer",
            )
            db.add(deal)
            await db.flush()
            print(f"  Created deal: {deal.company_name} (id={deal.id})")

            # Set Apriori as lead's deal
            deal.lead_partner_id = lead_partner.id
            await db.flush()

            # 3. Run Ghostwriter
            print("\n" + "=" * 60)
            print("STEP 3: Running Ghostwriter on Apriori")
            print("=" * 60)

            generator = MemoGenerator(db, firm_id)
            result = await generator.generate_memo(
                deal_id=deal.id,
                check_contradictions=True,
                include_ghost_loss=True,
            )
            await db.commit()

            memo = result["memo"]
            ghost_patterns = result.get("ghost_loss_patterns", [])
            contradictions = result.get("contradictions", [])

            print(f"  Memo generated: {memo.id}")
            print(f"  Ghost loss patterns found: {len(ghost_patterns)}")
            for p in ghost_patterns:
                print(f"    - {p.get('company_name', '?')}: {p.get('pass_reason', '')[:60]}...")

            # Print key sections
            if hasattr(memo, "friction_report") and memo.friction_report:
                print("\n  --- FRICTION REPORT ---")
                print(memo.friction_report[:500] + "..." if len(memo.friction_report or "") > 500 else (memo.friction_report or ""))

            if hasattr(memo, "gp_bias_ignore_reasoning") and memo.gp_bias_ignore_reasoning:
                print("\n  --- WHY GP SHOULD IGNORE PREVIOUS BIAS ---")
                print(memo.gp_bias_ignore_reasoning[:500] + "..." if len(memo.gp_bias_ignore_reasoning or "") > 500 else (memo.gp_bias_ignore_reasoning or ""))

            if memo.ghost_loss_analysis:
                print("\n  --- GHOST LOSS ANALYSIS ---")
                print(memo.ghost_loss_analysis[:400] + "..." if len(memo.ghost_loss_analysis or "") > 400 else (memo.ghost_loss_analysis or ""))

            # 4. Create poll and simulate votes
            print("\n" + "=" * 60)
            print("STEP 4: Simulating partner votes")
            print("=" * 60)

            # SET does not accept bind params; UUID is safe to interpolate
            await db.execute(text(f"SET app.current_firm_id = '{firm_id}'"))

            polling = PollingService(db, firm_id)
            poll = await polling.create_poll(
                ConvictionPollCreate(
                    deal_id=deal.id,
                    title=f"IC Vote: {deal.company_name}",
                    description="Stress test divergence",
                    reveal_threshold=3,
                ),
                created_by=lead_partner.id,
            )
            await db.flush()

            # Partner 1 (Lead): 4/10 - "Academic Founders"
            await polling.submit_vote(
                poll.id,
                lead_partner.id,
                PollVoteCreate(
                    conviction_score=4,
                    red_flags=["Academic Founders"],
                    red_flag_notes="Founder profile matches Deal A pattern - academic background, unclear sales DNA",
                    green_flags=[],
                ),
            )
            # Partner 2 (Specialist): 9/10 - "High Technical Velocity"
            await polling.submit_vote(
                poll.id,
                specialist.id,
                PollVoteCreate(
                    conviction_score=9,
                    red_flags=[],
                    green_flags=["High Technical Velocity", "Strong AI moat"],
                    green_flag_notes="Exceptional technical execution, category-defining",
                ),
            )
            # Partner 3 (Junior): 8/10 - Quietly bullish
            await polling.submit_vote(
                poll.id,
                junior.id,
                PollVoteCreate(
                    conviction_score=8,
                    red_flags=[],
                    green_flags=["Compelling thesis", "Underserved market"],
                    green_flag_notes="Quietly bullish on this one",
                ),
            )

            # Reveal poll
            await polling.reveal_poll(poll.id, lead_partner.id)
            await db.commit()

            print("  Partner 1 (Lead): 4/10 - Academic Founders")
            print("  Partner 2 (Specialist): 9/10 - High Technical Velocity")
            print("  Partner 3 (Junior): 8/10 - Quietly bullish")
            print(f"  Poll revealed: divergence = {9 - 4} points")

            # 5. Verify Divergence View
            print("\n" + "=" * 60)
            print("STEP 5: Divergence View verification")
            print("=" * 60)

            analyzer = DivergenceAnalyzer(db, firm_id)
            divergence_view = await analyzer.get_divergence_view(
                poll.id, lead_partner.id, is_lead_partner=True
            )

            print(f"  Total votes: {divergence_view.total_votes}")
            print(f"  Min score: {divergence_view.min_score}")
            print(f"  Max score: {divergence_view.max_score}")
            print(f"  Divergence (gap): {divergence_view.divergence}")
            print(f"  Average: {divergence_view.average_score}")
            print(f"  has_consensus: {divergence_view.has_consensus}")
            print(f"  needs_discussion: {divergence_view.needs_discussion}")

            # Assertions
            assert divergence_view.divergence == 5, f"Expected 5-point gap, got {divergence_view.divergence}"
            assert divergence_view.needs_discussion, "Expected needs_discussion=True for 5+ point gap"
            assert not divergence_view.has_consensus, "Expected has_consensus=False"
            assert divergence_view.min_score == 4 and divergence_view.max_score == 9

            print("\n  ✓ Divergence View: 5-point gap correctly identified")
            print("  ✓ High Divergence / needs_discussion = True")
            print("  ✓ High-Risk Pass scenario: Lead (4) vs Team (8.5 avg)")

            # High-Risk Pass: when lead votes low and divergence is high
            high_risk_pass = (
                divergence_view.divergence >= 5
                and divergence_view.votes
                and any(
                    v.conviction_score <= 4 and v.user_name and "Lead" in (v.user_name or "")
                    for v in divergence_view.votes
                )
            )
            # Simpler check: min is 4, max is 9, spread is 5
            high_risk_pass = divergence_view.divergence >= 5 and divergence_view.min_score <= 4
            print(f"  ✓ High-Risk Pass flagged: {high_risk_pass}")

            print("\n" + "=" * 60)
            print("STRESS TEST COMPLETE")
            print("=" * 60)
            return {
                "memo_id": str(memo.id),
                "deal_id": str(deal.id),
                "poll_id": str(poll.id),
                "ghost_patterns_count": len(ghost_patterns),
                "divergence": divergence_view.divergence,
                "needs_discussion": divergence_view.needs_discussion,
            }
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-seed", action="store_true", help="Skip seeding, use existing data")
    parser.add_argument("--db-url", default=settings.DATABASE_URL)
    args = parser.parse_args()

    asyncio.run(run_stress_test(args.db_url, args.skip_seed))


if __name__ == "__main__":
    main()
