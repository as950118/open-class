from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.permissions.auth import get_current_user
from app.schemas.auth import LoginRequest, UserRead

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).options(joinedload(User.academy)).where(User.email == str(payload.email).lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호를 확인해 주세요.")
    if user.academy_id is not None and user.academy.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="학원 계정이 이용 중지 상태입니다.")
    response.set_cookie(
        key="access_token",
        value=create_access_token(user.id),
        max_age=settings.jwt_expiration_hours * 3600,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="strict",
        path="/",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/", httponly=True, samesite="strict")


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user
