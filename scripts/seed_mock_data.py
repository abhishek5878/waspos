#!/usr/bin/env python3
"""
Seed mock data for Ghost Loss Detection stress test.

Creates:
- 1 firm (Wasp Ventures)
- 3 users (Lead Partner, Specialist, Junior)
- 3 historical PASS deals with IC memos in pgvector:
  - Deal A: Passed - "Founder is too academic, lacks sales grit"
  - Deal B: Passed - "Market size for AI-native dev tools is too small in India"
  - Deal C: Passed - "Valuation of $20M at Seed is too rich for our discipline"

Usage:
    cd backend && python -m scripts.seed_mock_data [--db-url URL] [--firm-id UUID]
    
Note: If RLS is enabled, ensure app.current_firm_id is set for your session.
      For first-time seeding, you may need to run as a DB superuser or ensure
      firms table has an appropriate INSERT policy.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add backend to path (run from project root: PYTHONPATH=backend python3 scripts/seed_mock_data.py)
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.pgbouncer import get_pgbouncer_connect_args

from app.core.config import settings
from app.models.firm import Firm
from app.models.user import User, UserRole
from app.models.deal import Deal, DealStage, DealSource
from app.models.document import Document, DocumentType
from app.services.memory.vector_store import VectorStore


# Historical Pass memo content - designed for vector similarity with Apriori
# (AI-native, academic founders, India market, valuation)
HISTORICAL_MEMOS = [
    {
        "company": "Deal A - AcademicFounders Inc",
        "deal_name": "AcademicFounders Inc",
        "sector": "Enterprise SaaS",
        "pass_reason": "Founder is too academic, lacks sales grit.",
        "memo_content": """IC MEMO - PASS RECOMMENDATION
Company: AcademicFounders Inc
Sector: Enterprise SaaS

RECOMMENDATION: Pass

KEY CONCERNS - WHY WE ARE PASSING:
The founding team consists of PhD researchers from top universities. While technically brilliant, 
we have concerns about commercial execution. Founder is too academic, lacks sales grit. 
Our experience suggests that pure academic backgrounds without demonstrated go-to-market 
ability often struggle in enterprise sales. The team has published extensively but has 
no prior startup or sales experience.

We have passed on similar deals where founders lacked commercial DNA. This pattern has 
cost us in the past when we over-indexed on technical credentials.
""",
    },
    {
        "company": "Deal B - DevTools India",
        "deal_name": "DevTools India",
        "sector": "AI Developer Tools",
        "pass_reason": "Market size for AI-native dev tools is too small in India.",
        "memo_content": """IC MEMO - PASS RECOMMENDATION
Company: DevTools India
Sector: AI Developer Tools

RECOMMENDATION: Pass

KEY CONCERNS - WHY WE ARE PASSING:
Market size for AI-native dev tools is too small in India. While the team has built 
impressive technology, the addressable market for AI developer tools in the Indian 
market specifically is constrained. Our TAM analysis suggests the India-only opportunity 
is under $500M. We typically look for larger initial markets.

We have passed on similar AI-native dev tool companies targeting India-first due to 
market size concerns. Global expansion would be required but adds execution risk.
""",
    },
    {
        "company": "Deal C - SeedRich Corp",
        "deal_name": "SeedRich Corp",
        "sector": "Infrastructure",
        "pass_reason": "Valuation of $20M at Seed is too rich for our discipline.",
        "memo_content": """IC MEMO - PASS RECOMMENDATION
Company: SeedRich Corp
Sector: Infrastructure

RECOMMENDATION: Pass

KEY CONCERNS - WHY WE ARE PASSING:
Valuation of $20M at Seed is too rich for our discipline. The company is pre-revenue 
with a prototype. While the technology is promising, we cannot justify this valuation 
for a Seed stage company. Our fund discipline requires more reasonable entry points 
at early stage.

We have consistently passed on deals where valuation at Seed exceeded our comfort level. 
Discipline on entry valuation has been a key differentiator for our returns.
""",
    },
]


async def seed_mock_data(db_url: str, firm_id_arg: Optional[str] = None):
    """Seed the database with mock historical pass memos."""
    engine = create_async_engine(db_url, connect_args=get_pgbouncer_connect_args())
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        try:
            from sqlalchemy import select

            # Get or create firm
            firm = None
            if firm_id_arg:
                from uuid import UUID
                firm = await db.get(Firm, UUID(firm_id_arg))
                if not firm:
                    raise ValueError(f"Firm {firm_id_arg} not found")
            else:
                result = await db.execute(select(Firm).limit(1))
                firm = result.scalar_one_or_none()

            if not firm:
                # Set minimal RLS context for bootstrap (may not work with strict RLS)
                await db.execute(text("SET app.current_firm_id = '00000000-0000-0000-0000-000000000000'"))
                firm = Firm(
                    name="Wasp Ventures",
                    slug="wasp-ventures",
                    description="Stress test firm for Ghost Loss Detection",
                    investment_thesis="B2B SaaS, AI-native tools, strong technical teams",
                    focus_sectors='["AI/ML", "Developer Tools", "Enterprise SaaS"]',
                    stage_preference="Seed to Series A",
                    typical_check_size="$1-3M",
                    red_flags="Academic founders without sales DNA; India-only market; rich seed valuations",
                )
                db.add(firm)
                await db.flush()
                print(f"Created firm: {firm.name} ({firm.id})")
            else:
                print(f"Using existing firm: {firm.name} ({firm.id})")

            firm_id = firm.id
            # SET does not accept bind params; UUID is safe to interpolate
            await db.execute(text(f"SET app.current_firm_id = '{firm_id}'"))

            # Create users if not exist
            users_data = [
                ("lead@wasp.vc", "Lead Partner", UserRole.PARTNER),
                ("specialist@wasp.vc", "Technical Specialist", UserRole.PRINCIPAL),
                ("junior@wasp.vc", "Junior Associate", UserRole.ASSOCIATE),
            ]

            import bcrypt
            hashed = bcrypt.hashpw(b"testpassword123", bcrypt.gensalt()).decode()

            users = []
            for email, name, role in users_data:
                result = await db.execute(
                    select(User).where(User.email == email, User.firm_id == firm_id)
                )
                user = result.scalar_one_or_none()
                if not user:
                    user = User(
                        firm_id=firm_id,
                        email=email,
                        hashed_password=hashed,
                        full_name=name,
                        role=role,
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()
                    print(f"  Created user: {name}")
                users.append(user)

            lead_partner, specialist, junior = users

            # Create 3 passed deals + IC memo documents with vectorized chunks
            vector_store = VectorStore(db, firm_id)

            for i, memo_data in enumerate(HISTORICAL_MEMOS):
                # Create Pass deal
                deal = Deal(
                    firm_id=firm_id,
                    company_name=memo_data["deal_name"],
                    one_liner=memo_data["sector"],
                    sector=memo_data["sector"],
                    stage=DealStage.PASSED,
                    source=DealSource.INBOUND,
                    pass_reason=memo_data["pass_reason"],
                )
                db.add(deal)
                await db.flush()

                # Create IC memo document
                doc = Document(
                    firm_id=firm_id,
                    deal_id=deal.id,
                    filename=f"ic_memo_{memo_data['deal_name'].replace(' ', '_')}.txt",
                    original_filename=f"IC_Memo_{memo_data['deal_name']}.txt",
                    file_path=f"/mocks/{memo_data['deal_name']}.txt",
                    document_type=DocumentType.IC_MEMO,
                    is_processed="yes",
                    extracted_company=memo_data["deal_name"],
                )
                db.add(doc)
                await db.flush()

                # Chunk and embed - content must include pass/concern/risk for vector search
                chunks = _chunk_memo(memo_data["memo_content"])
                for chunk in chunks:
                    chunk["section_type"] = "ic_memo"

                await vector_store.add_chunks(doc.id, chunks)
                print(f"  Indexed Deal {chr(65+i)}: {memo_data['deal_name']} - {len(chunks)} chunks")

            await db.commit()
            print(f"\n✓ Seeded 3 historical Pass memos for firm {firm_id}")
            return firm_id

        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise


def _chunk_memo(text: str, chunk_size: int = 800, overlap: int = 150) -> list[dict]:
    """Split memo text into overlapping chunks for embedding."""
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            para_break = text.rfind("\n\n", start, end)
            if para_break > start + chunk_size // 2:
                end = para_break
            else:
                sentence_break = text.rfind(". ", start, end)
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "chunk_index": chunk_index,
                "content": chunk_text,
            })
            chunk_index += 1

        start = end - overlap if end < len(text) else len(text)

    return chunks


def main():
    parser = argparse.ArgumentParser(description="Seed mock data for Ghost Loss stress test")
    parser.add_argument("--db-url", default=settings.DATABASE_URL)
    parser.add_argument("--firm-id", help="Use existing firm UUID (skips firm creation)")
    args = parser.parse_args()

    asyncio.run(seed_mock_data(args.db_url, args.firm_id))


if __name__ == "__main__":
    main()
