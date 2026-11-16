import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_teachers_id_academy_id"),
        UniqueConstraint("user_id", name="uq_teachers_user_id"),
        ForeignKeyConstraint(["user_id", "academy_id"], ["users.id", "users.academy_id"], ondelete="RESTRICT", name="fk_teachers_user_academy"),
        CheckConstraint("employment_status IN ('ACTIVE', 'ON_LEAVE', 'RESIGNED')", name="ck_teachers_employment_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    employment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
