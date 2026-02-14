import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Firm(Base):
    """VC Firm entity - top-level tenant for data isolation."""

    __tablename__ = "firms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Firm identity for Ghostwriter
    investment_thesis = Column(Text, nullable=True)
    focus_sectors = Column(Text, nullable=True)  # JSON array as text
    stage_preference = Column(String(100), nullable=True)  # Seed, Series A, etc.
    typical_check_size = Column(String(100), nullable=True)
    red_flags = Column(Text, nullable=True)  # Historical patterns to avoid

    # Configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="firm", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="firm", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="firm", cascade="all, delete-orphan")
    memo_templates = relationship("MemoTemplate", back_populates="firm", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Firm {self.name}>"
