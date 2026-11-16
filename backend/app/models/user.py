import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ACADEMY_ADMIN = "ACADEMY_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("id", "academy_id", name="uq_users_id_academy_id"),
        CheckConstraint("role IN ('SUPER_ADMIN', 'ACADEMY_ADMIN', 'TEACHER', 'STUDENT')", name="ck_users_role"),
        CheckConstraint("(role = 'SUPER_ADMIN' AND academy_id IS NULL) OR (role != 'SUPER_ADMIN' AND academy_id IS NOT NULL)", name="ck_user_academy_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("academies.id", ondelete="RESTRICT"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False, length=30), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    academy: Mapped["Academy | None"] = relationship(back_populates="users")

    @property
    def academy_name(self) -> str | None:
        return self.academy.name if self.academy else None
