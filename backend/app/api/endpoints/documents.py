from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
from pathlib import Path

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.document import Document, DocumentType
from app.schemas.document import DocumentUploadResponse, DeckExtractionResult
from app.services.memory.deck_extractor import DeckExtractor
from app.services.memory.pdf_parser import PDFParser
from app.services.memory.vector_store import VectorStore

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    deal_id: Optional[UUID] = Form(None),
    document_type: DocumentType = Form(DocumentType.PITCH_DECK),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload a document (PDF, DOCX, PPTX)."""
    firm_id = current_user["firm_id"]

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / str(firm_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    import uuid
    filename = f"{uuid.uuid4()}{ext}"
    file_path = upload_dir / filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create document record
    doc = Document(
        firm_id=firm_id,
        deal_id=deal_id,
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        document_type=document_type,
    )
    db.add(doc)
    await db.flush()

    return doc


@router.post("/{document_id}/process", response_model=DeckExtractionResult)
async def process_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Process a document: parse, extract data, and create embeddings."""
    firm_id = current_user["firm_id"]

    doc = await db.get(Document, document_id)
    if not doc or doc.firm_id != firm_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Read file content
    async with aiofiles.open(doc.file_path, "rb") as f:
        content = await f.read()

    # Extract deck data
    extractor = DeckExtractor()
    extracted = await extractor.extract_from_pdf(content, doc.original_filename)

    # Parse and chunk for embeddings
    parser = PDFParser()
    parsed = await parser.parse_bytes(content, doc.original_filename)
    chunks = parser.chunk_text(parsed["full_text"])

    # Add page numbers to chunks
    for chunk in chunks:
        chunk["page_number"] = 1  # Would need better page tracking

    # Store embeddings
    vector_store = VectorStore(db, firm_id)
    await vector_store.add_chunks(document_id, chunks)

    # Update document record
    doc.is_processed = "yes"
    doc.page_count = extracted.get("page_count", 0)
    doc.extracted_title = extracted.get("company_name")
    doc.extracted_company = extracted.get("company_name")
    doc.extraction_metadata = extracted

    # Update linked deal if exists
    if doc.deal_id:
        from app.models.deal import Deal
        deal = await db.get(Deal, doc.deal_id)
        if deal:
            if extracted.get("company_name"):
                deal.company_name = extracted["company_name"]
            if extracted.get("one_liner"):
                deal.one_liner = extracted["one_liner"]
            if extracted.get("team_summary"):
                deal.team_summary = extracted["team_summary"]
            if extracted.get("tam_analysis"):
                deal.tam_analysis = extracted["tam_analysis"]
            if extracted.get("moat_description"):
                deal.moat_description = extracted["moat_description"]
            if extracted.get("traction_metrics"):
                deal.traction_metrics = extracted["traction_metrics"]

    await db.flush()

    return DeckExtractionResult(
        document_id=document_id,
        company_name=extracted.get("company_name"),
        one_liner=extracted.get("one_liner"),
        team_summary=extracted.get("team_summary"),
        tam_analysis=extracted.get("tam_analysis"),
        moat_description=extracted.get("moat_description"),
        traction_metrics=extracted.get("traction_metrics"),
        founded_year=extracted.get("founded_year"),
        location=extracted.get("location"),
        funding_stage=extracted.get("funding_stage"),
        ask_amount=extracted.get("ask_amount"),
        page_count=extracted.get("page_count", 0),
        extraction_confidence=extracted.get("extraction_confidence", 0),
        sections_found=extracted.get("sections_found", []),
    )


@router.post("/search")
async def semantic_search(
    query: str,
    limit: int = 10,
    deal_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Semantic search across firm's documents."""
    firm_id = current_user["firm_id"]

    vector_store = VectorStore(db, firm_id)
    results = await vector_store.similarity_search(
        query=query,
        limit=limit,
        document_id=deal_id,
    )

    return {"results": results, "query": query, "count": len(results)}
