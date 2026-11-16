import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class LessonSession(Base):
    __tablename__ = "lesson_sessions"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_lesson_sessions_id_academy_id"),
        UniqueConstraint("schedule_id", "scheduled_at", name="uq_lesson_sessions_schedule_start"),
        ForeignKeyConstraint(["course_id", "academy_id"], ["courses.id", "courses.academy_id"], ondelete="RESTRICT", name="fk_lesson_sessions_course_academy"),
        ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_lesson_sessions_teacher_academy"),
        ForeignKeyConstraint(["schedule_id", "academy_id"], ["schedules.id", "schedules.academy_id"], ondelete="RESTRICT", name="fk_lesson_sessions_schedule_academy"),
        CheckConstraint("status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')", name="ck_lesson_sessions_status"),
        CheckConstraint("ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at", name="ck_lesson_sessions_time_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PLANNED", server_default="PLANNED", index=True)
    room: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LessonSessionStudent(Base):
    __tablename__ = "lesson_session_students"
    __table_args__ = (
        UniqueConstraint("lesson_session_id", "student_id", name="uq_lesson_session_student"),
        ForeignKeyConstraint(["lesson_session_id", "academy_id"], ["lesson_sessions.id", "lesson_sessions.academy_id"], ondelete="CASCADE", name="fk_session_students_session_academy"),
        ForeignKeyConstraint(["student_id", "academy_id"], ["students.id", "students.academy_id"], ondelete="RESTRICT", name="fk_session_students_student_academy"),
        CheckConstraint("attendance_status IN ('SCHEDULED', 'PRESENT', 'ABSENT', 'LATE', 'EXCUSED')", name="ck_lesson_session_students_attendance"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), nullable=False, index=True)
    lesson_session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    attendance_status: Mapped[str] = mapped_column(String(20), nullable=False, default="SCHEDULED", server_default="SCHEDULED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
