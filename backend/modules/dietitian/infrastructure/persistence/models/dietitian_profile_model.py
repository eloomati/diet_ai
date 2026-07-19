from datetime import datetime
from uuid import uuid4

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database.postgres import Base


class DietitianProfileModel(Base):
    __tablename__ = "dietitian_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    experience: Mapped[str] = mapped_column(Text, nullable=False)
    diplomas: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photos: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
