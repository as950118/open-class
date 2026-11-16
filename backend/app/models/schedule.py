import uuid
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_schedules_id_academy_id"),
        ForeignKeyConstraint(["course_id", "academy_id"], ["courses.id", "courses.academy_id"], ondelete="RESTRICT", name="fk_schedules_course_academy"),
        ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_schedules_teacher_academy"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_schedules_day_of_week"),
        CheckConstraint("start_time < end_time", name="ck_schedules_time_range"),
        CheckConstraint("effective_end_date IS NULL OR effective_end_date >= effective_start_date", name="ck_schedules_date_range"),
        CheckConstraint("status IN ('ACTIVE', 'CANCELLED')", name="ck_schedules_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(), nullable=False)
    effective_start_date: Mapped[date] = mapped_column(Date(), nullable=False)
    effective_end_date: Mapped[date | None] = mapped_column(Date())
    room: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
