import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_enrollments_id_academy_id"),
        UniqueConstraint("academy_id", "course_id", "student_id", name="uq_enrollments_course_student"),
        ForeignKeyConstraint(["course_id", "academy_id"], ["courses.id", "courses.academy_id"], ondelete="RESTRICT", name="fk_enrollments_course_academy"),
        ForeignKeyConstraint(["student_id", "academy_id"], ["students.id", "students.academy_id"], ondelete="RESTRICT", name="fk_enrollments_student_academy"),
        CheckConstraint("status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')", name="ck_enrollments_status"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_enrollments_date_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
