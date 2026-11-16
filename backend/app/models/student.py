import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_students_id_academy_id"),
        UniqueConstraint("user_id", name="uq_students_user_id"),
        ForeignKeyConstraint(["user_id", "academy_id"], ["users.id", "users.academy_id"], ondelete="RESTRICT", name="fk_students_user_academy"),
        CheckConstraint("status IN ('ACTIVE', 'PAUSED', 'WITHDRAWN')", name="ck_students_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    birth_date: Mapped[date | None] = mapped_column(Date)
    guardian_name: Mapped[str | None] = mapped_column(String(100))
    guardian_phone: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE", index=True)
    memo: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
