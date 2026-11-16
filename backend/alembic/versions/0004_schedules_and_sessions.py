"""Add recurring schedules, dated lesson sessions and attendance.

Revision ID: 0004_schedules_sessions
Revises: 0003_academy_data
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_schedules_sessions"
down_revision = "0003_academy_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("effective_start_date", sa.Date(), nullable=False),
        sa.Column("effective_end_date", sa.Date()),
        sa.Column("room", sa.String(length=80)),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_schedules_academy_id_academies"),
        sa.ForeignKeyConstraint(["course_id", "academy_id"], ["courses.id", "courses.academy_id"], ondelete="RESTRICT", name="fk_schedules_course_academy"),
        sa.ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_schedules_teacher_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_schedules_id_academy_id"),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_schedules_day_of_week"),
        sa.CheckConstraint("start_time < end_time", name="ck_schedules_time_range"),
        sa.CheckConstraint("effective_end_date IS NULL OR effective_end_date >= effective_start_date", name="ck_schedules_date_range"),
        sa.CheckConstraint("status IN ('ACTIVE', 'CANCELLED')", name="ck_schedules_status"),
    )
    op.create_index("ix_schedules_academy_id", "schedules", ["academy_id"])
    op.create_index("ix_schedules_course_id", "schedules", ["course_id"])
    op.create_index("ix_schedules_teacher_id", "schedules", ["teacher_id"])
    op.create_index("ix_schedules_status", "schedules", ["status"])

    op.create_table(
        "lesson_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("schedule_id", sa.Uuid()),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=20), server_default="PLANNED", nullable=False),
        sa.Column("room", sa.String(length=80)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_lesson_sessions_academy_id_academies"),
        sa.ForeignKeyConstraint(["course_id", "academy_id"], ["courses.id", "courses.academy_id"], ondelete="RESTRICT", name="fk_lesson_sessions_course_academy"),
        sa.ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_lesson_sessions_teacher_academy"),
        sa.ForeignKeyConstraint(["schedule_id", "academy_id"], ["schedules.id", "schedules.academy_id"], ondelete="RESTRICT", name="fk_lesson_sessions_schedule_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_lesson_sessions_id_academy_id"),
        sa.UniqueConstraint("schedule_id", "scheduled_at", name="uq_lesson_sessions_schedule_start"),
        sa.CheckConstraint("status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')", name="ck_lesson_sessions_status"),
        sa.CheckConstraint("ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at", name="ck_lesson_sessions_time_range"),
    )
    op.create_index("ix_lesson_sessions_academy_id", "lesson_sessions", ["academy_id"])
    op.create_index("ix_lesson_sessions_course_id", "lesson_sessions", ["course_id"])
    op.create_index("ix_lesson_sessions_teacher_id", "lesson_sessions", ["teacher_id"])
    op.create_index("ix_lesson_sessions_schedule_id", "lesson_sessions", ["schedule_id"])
    op.create_index("ix_lesson_sessions_scheduled_at", "lesson_sessions", ["scheduled_at"])
    op.create_index("ix_lesson_sessions_status", "lesson_sessions", ["status"])

    op.create_table(
        "lesson_session_students",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_session_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("attendance_status", sa.String(length=20), server_default="SCHEDULED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_lesson_session_students_academy_id_academies"),
        sa.ForeignKeyConstraint(["lesson_session_id", "academy_id"], ["lesson_sessions.id", "lesson_sessions.academy_id"], ondelete="CASCADE", name="fk_session_students_session_academy"),
        sa.ForeignKeyConstraint(["student_id", "academy_id"], ["students.id", "students.academy_id"], ondelete="RESTRICT", name="fk_session_students_student_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_session_id", "student_id", name="uq_lesson_session_student"),
        sa.CheckConstraint("attendance_status IN ('SCHEDULED', 'PRESENT', 'ABSENT', 'LATE', 'EXCUSED')", name="ck_lesson_session_students_attendance"),
    )
    op.create_index("ix_lesson_session_students_academy_id", "lesson_session_students", ["academy_id"])
    op.create_index("ix_lesson_session_students_lesson_session_id", "lesson_session_students", ["lesson_session_id"])
    op.create_index("ix_lesson_session_students_student_id", "lesson_session_students", ["student_id"])


def downgrade() -> None:
    for table, indexes in (
        ("lesson_session_students", ("ix_lesson_session_students_student_id", "ix_lesson_session_students_lesson_session_id", "ix_lesson_session_students_academy_id")),
        ("lesson_sessions", ("ix_lesson_sessions_status", "ix_lesson_sessions_scheduled_at", "ix_lesson_sessions_schedule_id", "ix_lesson_sessions_teacher_id", "ix_lesson_sessions_course_id", "ix_lesson_sessions_academy_id")),
        ("schedules", ("ix_schedules_status", "ix_schedules_teacher_id", "ix_schedules_course_id", "ix_schedules_academy_id")),
    ):
        for index in indexes:
            op.drop_index(index, table_name=table)
        op.drop_table(table)
