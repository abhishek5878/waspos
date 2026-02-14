import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserRole(str, Enum):
    """User roles within a firm."""
    ADMIN = "admin"
    PARTNER = "partner"
    PRINCIPAL = "principal"
    ASSOCIATE = "associate"
    ANALYST = "analyst"


class User(Base):
    """User entity - belongs to a single firm."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firm_id = Column(UUID(as_uuid=True), ForeignKey("firms.id"), nullable=False, index=True)

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable if using Clerk
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ANALYST)

    # Clerk integration
    clerk_user_id = Column(String(255), unique=True, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    firm = relationship("Firm", back_populates="users")
    led_deals = relationship("Deal", back_populates="lead_partner", foreign_keys="Deal.lead_partner_id")
    poll_votes = relationship("PollVote", back_populates="user", cascade="all, delete-orphan")
    authored_memos = relationship("InvestmentMemo", back_populates="author")

    def __repr__(self):
        return f"<User {self.email}>"
