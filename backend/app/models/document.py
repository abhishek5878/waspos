import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db.session import Base
from app.core.config import settings


class DocumentType(str, Enum):
    """Type of document."""
    PITCH_DECK = "pitch_deck"
    IC_MEMO = "ic_memo"
    FINANCIAL_MODEL = "financial_model"
    DATA_ROOM = "data_room"
    TERM_SHEET = "term_sheet"
    OTHER = "other"


class Document(Base):
    """Uploaded document linked to a deal."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=True, index=True)

    # File info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER)

    # Processing status
    is_processed = Column(String(10), default="no")
    processing_error = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)

    # Extracted metadata
    extracted_title = Column(String(500), nullable=True)
    extracted_company = Column(String(255), nullable=True)
    extracted_date = Column(DateTime, nullable=True)
    extraction_metadata = Column(JSONB, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    firm = relationship("Firm", back_populates="documents")
    deal = relationship("Deal", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.original_filename}>"


class DocumentChunk(Base):
    """Vector-embedded chunk of a document for semantic search."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)

    # Vector embedding (pgvector)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)

    # Extra chunk metadata (column named chunk_metadata to avoid SQLAlchemy reserved "metadata")
    section_type = Column(String(100), nullable=True)  # "team", "market", "traction"
    chunk_metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk {self.chunk_index}>"
