from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.deal import DealStage, DealSource


class TractionMetrics(BaseModel):
    """Extracted traction metrics from pitch deck."""
    mrr: Optional[Decimal] = None
    arr: Optional[Decimal] = None
    growth_rate: Optional[float] = None
    customers: Optional[int] = None
    gmv: Optional[Decimal] = None
    dau: Optional[int] = None
    mau: Optional[int] = None
    nrr: Optional[float] = None  # Net Revenue Retention
    custom_metrics: Optional[dict] = None


class DealBase(BaseModel):
    """Base deal schema."""
    company_name: str = Field(..., min_length=1, max_length=255)
    website: Optional[str] = None
    description: Optional[str] = None
    one_liner: Optional[str] = Field(None, max_length=500)
    sector: Optional[str] = Field(None, max_length=100)
    sub_sector: Optional[str] = Field(None, max_length=100)
    source: DealSource = DealSource.INBOUND
    referrer: Optional[str] = None


class DealCreate(DealBase):
    """Schema for creating a new deal."""
    lead_partner_id: Optional[UUID] = None
    asking_valuation: Optional[Decimal] = None
    proposed_check: Optional[Decimal] = None
    round_size: Optional[Decimal] = None
    first_contact_date: Optional[datetime] = None


class DealUpdate(BaseModel):
    """Schema for updating a deal."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = None
    description: Optional[str] = None
    one_liner: Optional[str] = None
    stage: Optional[DealStage] = None
    source: Optional[DealSource] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    lead_partner_id: Optional[UUID] = None
    asking_valuation: Optional[Decimal] = None
    proposed_check: Optional[Decimal] = None
    round_size: Optional[Decimal] = None
    referrer: Optional[str] = None
    notes: Optional[str] = None
    pass_reason: Optional[str] = None
    ic_date: Optional[datetime] = None
    close_date: Optional[datetime] = None

    # Extracted deck data
    team_summary: Optional[str] = None
    tam_analysis: Optional[str] = None
    moat_description: Optional[str] = None
    traction_metrics: Optional[TractionMetrics] = None


class DealResponse(DealBase):
    """Schema for deal response."""
    id: UUID
    firm_id: UUID
    lead_partner_id: Optional[UUID] = None
    stage: DealStage
    asking_valuation: Optional[Decimal] = None
    proposed_check: Optional[Decimal] = None
    round_size: Optional[Decimal] = None
    team_summary: Optional[str] = None
    tam_analysis: Optional[str] = None
    moat_description: Optional[str] = None
    traction_metrics: Optional[dict] = None
    notes: Optional[str] = None
    pass_reason: Optional[str] = None
    first_contact_date: Optional[datetime] = None
    ic_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealListResponse(BaseModel):
    """Paginated list of deals."""
    deals: list[DealResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
