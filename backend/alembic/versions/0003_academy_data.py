"""Add tenant-scoped teachers, students, subjects, courses and enrollments.

Revision ID: 0003_academy_data
Revises: 0002_identity
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_academy_data"
down_revision = "0002_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_users_id_academy_id", "users", ["id", "academy_id"])

    op.create_table(
        "teachers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30)),
        sa.Column("employment_status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_teachers_academy_id_academies"),
        sa.ForeignKeyConstraint(["user_id", "academy_id"], ["users.id", "users.academy_id"], ondelete="RESTRICT", name="fk_teachers_user_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_teachers_id_academy_id"),
        sa.UniqueConstraint("user_id", name="uq_teachers_user_id"),
        sa.CheckConstraint("employment_status IN ('ACTIVE', 'ON_LEAVE', 'RESIGNED')", name="ck_teachers_employment_status"),
    )
    op.create_index("ix_teachers_academy_id", "teachers", ["academy_id"])

    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid()),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30)),
        sa.Column("email", sa.String(length=255)),
        sa.Column("birth_date", sa.Date()),
        sa.Column("guardian_name", sa.String(length=100)),
        sa.Column("guardian_phone", sa.String(length=30)),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("memo", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_students_academy_id_academies"),
        sa.ForeignKeyConstraint(["user_id", "academy_id"], ["users.id", "users.academy_id"], ondelete="RESTRICT", name="fk_students_user_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_students_id_academy_id"),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
        sa.CheckConstraint("status IN ('ACTIVE', 'PAUSED', 'WITHDRAWN')", name="ck_students_status"),
    )
    op.create_index("ix_students_academy_id", "students", ["academy_id"])
    op.create_index("ix_students_name", "students", ["name"])
    op.create_index("ix_students_status", "students", ["status"])

    op.create_table(
        "subjects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("color", sa.String(length=7), server_default="#6474E8", nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_subjects_academy_id_academies"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_subjects_id_academy_id"),
        sa.UniqueConstraint("academy_id", "name", name="uq_subjects_academy_name"),
    )
    op.create_index("ix_subjects_academy_id", "subjects", ["academy_id"])

    op.create_table(
        "courses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_courses_academy_id_academies"),
        sa.ForeignKeyConstraint(["subject_id", "academy_id"], ["subjects.id", "subjects.academy_id"], ondelete="RESTRICT", name="fk_courses_subject_academy"),
        sa.ForeignKeyConstraint(["teacher_id", "academy_id"], ["teachers.id", "teachers.academy_id"], ondelete="RESTRICT", name="fk_courses_teacher_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_courses_id_academy_id"),
        sa.CheckConstraint("status IN ('ACTIVE', 'PAUSED', 'CLOSED')", name="ck_courses_status"),
    )
    op.create_index("ix_courses_academy_id", "courses", ["academy_id"])
    op.create_index("ix_courses_subject_id", "courses", ["subject_id"])
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"])
    op.create_index("ix_courses_name", "courses", ["name"])
    op.create_index("ix_courses_status", "courses", ["status"])

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("academy_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="RESTRICT", name="fk_enrollments_academy_id_academies"),
        sa.ForeignKeyConstraint(["course_id", "academy_id"], ["courses.id", "courses.academy_id"], ondelete="RESTRICT", name="fk_enrollments_course_academy"),
        sa.ForeignKeyConstraint(["student_id", "academy_id"], ["students.id", "students.academy_id"], ondelete="RESTRICT", name="fk_enrollments_student_academy"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "academy_id", name="uq_enrollments_id_academy_id"),
        sa.UniqueConstraint("academy_id", "course_id", "student_id", name="uq_enrollments_course_student"),
        sa.CheckConstraint("status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')", name="ck_enrollments_status"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_enrollments_date_range"),
    )
    op.create_index("ix_enrollments_academy_id", "enrollments", ["academy_id"])
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])
    op.create_index("ix_enrollments_student_id", "enrollments", ["student_id"])
    op.create_index("ix_enrollments_status", "enrollments", ["status"])


def downgrade() -> None:
    for table, indexes in (
        ("enrollments", ("ix_enrollments_status", "ix_enrollments_student_id", "ix_enrollments_course_id", "ix_enrollments_academy_id")),
        ("courses", ("ix_courses_status", "ix_courses_name", "ix_courses_teacher_id", "ix_courses_subject_id", "ix_courses_academy_id")),
        ("subjects", ("ix_subjects_academy_id",)),
        ("students", ("ix_students_status", "ix_students_name", "ix_students_academy_id")),
        ("teachers", ("ix_teachers_academy_id",)),
    ):
        for index in indexes:
            op.drop_index(index, table_name=table)
        op.drop_table(table)
    op.drop_constraint("uq_users_id_academy_id", "users", type_="unique")
