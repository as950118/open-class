import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import hash_password
from app.models.academy import Academy
from app.models.user import User, UserRole
from app.permissions.auth import get_current_user, require_roles
from app.schemas.auth import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])
admin_roles = (UserRole.SUPER_ADMIN, UserRole.ACADEMY_ADMIN)


@router.get("", response_model=list[UserRead])
def list_users(
    academy_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    query = select(User).options(joinedload(User.academy)).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if user.role == UserRole.SUPER_ADMIN:
        if academy_id:
            query = query.where(User.academy_id == academy_id)
    elif user.role == UserRole.ACADEMY_ADMIN:
        query = query.where(User.academy_id == user.academy_id)
    else:
        return [user]
    return list(db.scalars(query).unique().all())


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    user: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> User:
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 이메일입니다.")

    if user.role == UserRole.ACADEMY_ADMIN:
        if user.academy_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="학원에 연결된 관리자 계정이 아닙니다.")
        if payload.role not in (UserRole.TEACHER, UserRole.STUDENT):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="선생님 또는 학생 계정만 등록할 수 있습니다.")
        academy_id = user.academy_id
    else:
        academy_id = payload.academy_id
        if payload.role != UserRole.SUPER_ADMIN and academy_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="학원 계정에는 academy_id가 필요합니다.")
        if payload.role == UserRole.SUPER_ADMIN and academy_id is not None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="플랫폼 관리자 계정은 학원에 소속될 수 없습니다.")

    if academy_id is not None and db.get(Academy, academy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="학원을 찾을 수 없습니다.")

    created = User(
        academy_id=academy_id,
        email=email,
        password_hash=hash_password(payload.password),
        name=payload.name.strip(),
        role=payload.role,
        is_active=True,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return db.scalar(select(User).options(joinedload(User.academy)).where(User.id == created.id))
import uuid

