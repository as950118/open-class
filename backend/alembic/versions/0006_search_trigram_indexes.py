"""Add pg_trgm indexes for academy-wide search fields.

Revision ID: 0006_search_trigram_indexes
Revises: 0005_lesson_logs
"""
from alembic import op

revision = "0006_search_trigram_indexes"
down_revision = "0005_lesson_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, column in (
        ("students", "name"),
        ("teachers", "name"),
        ("courses", "name"),
        ("subjects", "name"),
        ("lesson_logs", "subject"),
        ("lesson_logs", "homework"),
        ("lesson_logs", "feedback"),
        ("lesson_logs", "next_plan"),
    ):
        op.execute(f"CREATE INDEX ix_{table}_{column}_trgm ON {table} USING gin ({column} gin_trgm_ops)")


def downgrade() -> None:
    for table, column in (
        ("lesson_logs", "next_plan"),
        ("lesson_logs", "feedback"),
        ("lesson_logs", "homework"),
        ("lesson_logs", "subject"),
        ("subjects", "name"),
        ("courses", "name"),
        ("teachers", "name"),
        ("students", "name"),
    ):
        op.execute(f"DROP INDEX ix_{table}_{column}_trgm")
