from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.document import DocumentType


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: UUID
    firm_id: UUID
    deal_id: Optional[UUID] = None
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    is_processed: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DeckExtractionResult(BaseModel):
    """Extracted data from a pitch deck."""
    document_id: UUID

    # Core extracted fields
    company_name: Optional[str] = None
    one_liner: Optional[str] = None
    team_summary: Optional[str] = None
    tam_analysis: Optional[str] = None
    moat_description: Optional[str] = None
    traction_metrics: Optional[dict] = None

    # Additional extracted info
    founded_year: Optional[int] = None
    location: Optional[str] = None
    funding_stage: Optional[str] = None
    ask_amount: Optional[str] = None

    # Metadata
    page_count: int
    extraction_confidence: float
    sections_found: list[str]


class DocumentChunkResponse(BaseModel):
    """Response for a document chunk."""
    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    section_type: Optional[str] = None

    class Config:
        from_attributes = True


class SemanticSearchRequest(BaseModel):
    """Request for semantic search across documents."""
    query: str
    limit: int = 10
    document_types: Optional[list[DocumentType]] = None
    deal_id: Optional[UUID] = None
    min_similarity: float = 0.7


class SemanticSearchResult(BaseModel):
    """Result from semantic search."""
    chunk_id: UUID
    document_id: UUID
    deal_id: Optional[UUID] = None
    content: str
    similarity: float
    page_number: Optional[int] = None
    section_type: Optional[str] = None
    document_title: str
