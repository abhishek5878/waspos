from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.deal import Deal, DealStage
from app.schemas.deal import DealCreate, DealUpdate, DealResponse, DealListResponse

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/", response_model=DealResponse, status_code=201)
async def create_deal(
    data: DealCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new deal in the pipeline."""
    deal = Deal(
        firm_id=current_user["firm_id"],
        lead_partner_id=data.lead_partner_id,
        company_name=data.company_name,
        website=data.website,
        description=data.description,
        one_liner=data.one_liner,
        sector=data.sector,
        sub_sector=data.sub_sector,
        source=data.source,
        referrer=data.referrer,
        asking_valuation=data.asking_valuation,
        proposed_check=data.proposed_check,
        round_size=data.round_size,
        first_contact_date=data.first_contact_date,
    )
    db.add(deal)
    await db.flush()
    return deal


@router.get("/", response_model=DealListResponse)
async def list_deals(
    stage: Optional[DealStage] = None,
    sector: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List deals in the pipeline with filtering."""
    firm_id = current_user["firm_id"]

    # Build query
    query = select(Deal).where(Deal.firm_id == firm_id)

    if stage:
        query = query.where(Deal.stage == stage)
    if sector:
        query = query.where(Deal.sector == sector)
    if search:
        query = query.where(Deal.company_name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count(Deal.id)).where(Deal.firm_id == firm_id)
    if stage:
        count_query = count_query.where(Deal.stage == stage)
    if sector:
        count_query = count_query.where(Deal.sector == sector)
    if search:
        count_query = count_query.where(Deal.company_name.ilike(f"%{search}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.order_by(Deal.updated_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    deals = result.scalars().all()

    return DealListResponse(
        deals=[DealResponse.model_validate(d) for d in deals],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific deal."""
    deal = await db.get(Deal, deal_id)
    if not deal or deal.firm_id != current_user["firm_id"]:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    data: DealUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a deal."""
    deal = await db.get(Deal, deal_id)
    if not deal or deal.firm_id != current_user["firm_id"]:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deal, field, value)

    await db.flush()
    return deal


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a deal."""
    deal = await db.get(Deal, deal_id)
    if not deal or deal.firm_id != current_user["firm_id"]:
        raise HTTPException(status_code=404, detail="Deal not found")

    await db.delete(deal)
    await db.flush()


@router.post("/{deal_id}/stage/{stage}", response_model=DealResponse)
async def update_deal_stage(
    deal_id: UUID,
    stage: DealStage,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update deal stage."""
    deal = await db.get(Deal, deal_id)
    if not deal or deal.firm_id != current_user["firm_id"]:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal.stage = stage
    await db.flush()
    return deal
