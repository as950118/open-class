import uuid

from fastapi import HTTPException, status

from app.models.user import User, UserRole


def write_academy_id(user: User, requested_id: uuid.UUID | None) -> uuid.UUID:
    if user.role == UserRole.SUPER_ADMIN:
        if requested_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="academy_id가 필요합니다.")
        return requested_id
    if user.academy_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="학원에 연결된 계정이 아닙니다.")
    if requested_id is not None and requested_id != user.academy_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="다른 학원의 데이터에 접근할 수 없습니다.")
    return user.academy_id


def read_academy_filter(user: User, requested_id: uuid.UUID | None) -> uuid.UUID | None:
    if user.role == UserRole.SUPER_ADMIN:
        return requested_id
    if user.academy_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="학원에 연결된 계정이 아닙니다.")
    if requested_id is not None and requested_id != user.academy_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="다른 학원의 데이터에 접근할 수 없습니다.")
    return user.academy_id
