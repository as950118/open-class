from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole


def get_current_user(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    if not access_token:
        raise unauthorized
    try:
        payload = jwt.decode(access_token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    if user.academy_id is not None and user.academy.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="학원 계정이 이용 중지 상태입니다.")
    return user


def require_roles(*allowed_roles: UserRole) -> Callable:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 작업을 수행할 권한이 없습니다.")
        return user

    return dependency
