from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.memo import (
    GhostwriterRequest,
    GhostwriterResponse,
    InvestmentMemoResponse,
    GhostLossPattern,
)
from app.services.ghostwriter.memo_generator import MemoGenerator

router = APIRouter(prefix="/ghostwriter", tags=["ghostwriter"])


@router.post("/generate", response_model=GhostwriterResponse)
async def generate_memo(
    request: GhostwriterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate an IC memo using the Ghostwriter AI.

    The Ghostwriter analyzes:
    1. The pitch deck and deal data
    2. Historical pass patterns from similar deals
    3. Potential contradictions with past decisions

    It generates a comprehensive memo including a "Why This Might Be a Ghost Loss"
    section that challenges the team to confront potential blind spots.
    """
    firm_id = current_user["firm_id"]

    generator = MemoGenerator(db, firm_id)

    try:
        result = await generator.generate_memo(
            deal_id=request.deal_id,
            template_id=request.template_id,
            additional_context=request.additional_context,
            check_contradictions=request.check_contradictions,
            include_ghost_loss=request.include_ghost_loss,
        )

        # Convert ghost loss patterns to schema objects
        ghost_patterns = [
            GhostLossPattern(**p) for p in result.get("ghost_loss_patterns", [])
        ]

        return GhostwriterResponse(
            memo_id=result["memo_id"],
            memo=InvestmentMemoResponse.model_validate(result["memo"]),
            contradictions=result["contradictions"],
            ghost_loss_patterns=ghost_patterns,
            historical_memos_analyzed=len(ghost_patterns) + len(result.get("contradictions", [])),
            generation_time_seconds=result["generation_time_seconds"],
            tokens_used=result["tokens_used"],
            model_used=result["model_used"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memo generation failed: {str(e)}")


@router.get("/memos/{memo_id}", response_model=InvestmentMemoResponse)
async def get_memo(
    memo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific investment memo."""
    from app.models.memo import InvestmentMemo

    memo = await db.get(InvestmentMemo, memo_id)
    if not memo or memo.firm_id != current_user["firm_id"]:
        raise HTTPException(status_code=404, detail="Memo not found")

    return memo


@router.get("/deals/{deal_id}/memos")
async def get_deal_memos(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all memos for a deal."""
    from sqlalchemy import select
    from app.models.memo import InvestmentMemo

    result = await db.execute(
        select(InvestmentMemo)
        .where(
            InvestmentMemo.deal_id == deal_id,
            InvestmentMemo.firm_id == current_user["firm_id"],
        )
        .order_by(InvestmentMemo.created_at.desc())
    )
    memos = result.scalars().all()

    return {"memos": [InvestmentMemoResponse.model_validate(m) for m in memos]}
