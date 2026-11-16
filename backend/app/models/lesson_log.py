import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class LessonLog(Base):
    __tablename__ = "lesson_logs"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_lesson_logs_id_academy_id"),
        UniqueConstraint("lesson_session_id", "student_id", name="uq_lesson_logs_session_student"),
        ForeignKeyConstraint(["lesson_session_id", "academy_id"], ["lesson_sessions.id", "lesson_sessions.academy_id"], ondelete="CASCADE", name="fk_lesson_logs_session_academy"),
        ForeignKeyConstraint(["student_id", "academy_id"], ["students.id", "students.academy_id"], ondelete="RESTRICT", name="fk_lesson_logs_student_academy"),
        ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_lesson_logs_teacher_academy"),
        CheckConstraint("understanding_level IS NULL OR understanding_level BETWEEN 1 AND 5", name="ck_lesson_logs_understanding_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    lesson_session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(160))
    lesson_content: Mapped[str] = mapped_column(Text, nullable=False)
    progress_content: Mapped[str | None] = mapped_column(Text)
    understanding_level: Mapped[int | None] = mapped_column(Integer)
    homework: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    next_plan: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
