"""Create student-specific lesson logs.

Revision ID: 0005_lesson_logs
Revises: 0004_schedules_sessions
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_lesson_logs"
down_revision = "0004_schedules_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_session_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(160)),
        sa.Column("lesson_content", sa.Text(), nullable=False),
        sa.Column("progress_content", sa.Text()),
        sa.Column("understanding_level", sa.Integer()),
        sa.Column("homework", sa.Text()),
        sa.Column("feedback", sa.Text()),
        sa.Column("next_plan", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_lesson_logs_academy_id_academies"),
        sa.ForeignKeyConstraint(["lesson_session_id", "academy_id"], ["lesson_sessions.id", "lesson_sessions.academy_id"], ondelete="CASCADE", name="fk_lesson_logs_session_academy"),
        sa.ForeignKeyConstraint(["student_id", "academy_id"], ["students.id", "students.academy_id"], ondelete="RESTRICT", name="fk_lesson_logs_student_academy"),
        sa.ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_lesson_logs_teacher_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_lesson_logs_id_academy_id"),
        sa.UniqueConstraint("lesson_session_id", "student_id", name="uq_lesson_logs_session_student"),
        sa.CheckConstraint("understanding_level IS NULL OR understanding_level BETWEEN 1 AND 5", name="ck_lesson_logs_understanding_level"),
    )
    for col in ("academy_id", "lesson_session_id", "teacher_id", "student_id"):
        op.create_index(f"ix_lesson_logs_{col}", "lesson_logs", [col])
    op.execute("CREATE INDEX ix_lesson_logs_content_trgm ON lesson_logs USING gin (lesson_content gin_trgm_ops)")
    op.execute("CREATE INDEX ix_lesson_logs_progress_trgm ON lesson_logs USING gin (progress_content gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_lesson_logs_progress_trgm")
    op.execute("DROP INDEX IF EXISTS ix_lesson_logs_content_trgm")
    for col in ("student_id", "teacher_id", "lesson_session_id", "academy_id"):
        op.drop_index(f"ix_lesson_logs_{col}", table_name="lesson_logs")
    op.drop_table("lesson_logs")
