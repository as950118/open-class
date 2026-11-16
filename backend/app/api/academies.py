from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.academy import Academy
from app.models.user import User, UserRole
from app.permissions.auth import require_roles
from app.schemas.academy import AcademyCreate, AcademyRead

router = APIRouter(prefix="/academies", tags=["academies"])


@router.get("", response_model=list[AcademyRead])
def list_academies(
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> list[Academy]:
    return list(db.scalars(select(Academy).order_by(Academy.name)).all())


@router.post("", response_model=AcademyRead, status_code=status.HTTP_201_CREATED)
def create_academy(
    payload: AcademyCreate,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> Academy:
    if db.scalar(select(Academy.id).where(Academy.code == payload.code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 학원 코드입니다.")
    academy = Academy(name=payload.name.strip(), code=payload.code)
    db.add(academy)
    db.commit()
    db.refresh(academy)
    return academy
