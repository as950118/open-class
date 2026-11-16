import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.academy import Academy
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.permissions.auth import get_current_user, require_roles
from app.schemas.academy_data import StudentCreate, StudentRead, StudentUpdate, TeacherCreate, TeacherRead, TeacherUpdate
from app.services.tenancy import read_academy_filter, write_academy_id

router = APIRouter(tags=["academy people"])
admin_roles = (UserRole.SUPER_ADMIN, UserRole.ACADEMY_ADMIN)


def _teacher_read(teacher: Teacher, email: str) -> dict:
    return {"id": teacher.id, "academy_id": teacher.academy_id, "user_id": teacher.user_id, "email": email, "name": teacher.name, "phone": teacher.phone, "employment_status": teacher.employment_status}


@router.get("/teachers", response_model=list[TeacherRead])
def list_teachers(
    academy_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    if user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="선생님 목록을 조회할 권한이 없습니다.")
    academy_scope = read_academy_filter(user, academy_id)
    query = select(Teacher, User.email).join(User, User.id == Teacher.user_id).order_by(Teacher.name).limit(limit).offset(offset)
    if academy_scope:
        query = query.where(Teacher.academy_id == academy_scope)
    if user.role == UserRole.TEACHER:
        query = query.where(Teacher.user_id == user.id)
    if search:
        query = query.where(Teacher.name.ilike(f"%{search.strip()}%"))
    return [_teacher_read(teacher, email) for teacher, email in db.execute(query).all()]


@router.post("/teachers", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
def create_teacher(
    payload: TeacherCreate,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict:
    tenant_id = write_academy_id(actor, academy_id)
    academy = db.get(Academy, tenant_id)
    if academy is None:
        raise HTTPException(status_code=404, detail="학원을 찾을 수 없습니다.")
    if academy.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="이용 중지된 학원에는 프로필을 등록할 수 없습니다.")
    if payload.user_id is not None:
        linked_user = db.get(User, payload.user_id)
        if linked_user is None or linked_user.role != UserRole.TEACHER or linked_user.academy_id != tenant_id or not linked_user.is_active:
            raise HTTPException(status_code=422, detail="같은 학원의 활성 선생님 계정을 선택해 주세요.")
    else:
        email = str(payload.email).lower()
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
        linked_user = User(academy_id=tenant_id, email=email, name=payload.name.strip(), role=UserRole.TEACHER, password_hash=hash_password(payload.password))
        db.add(linked_user)
        db.flush()
    if db.scalar(select(Teacher.id).where(Teacher.user_id == linked_user.id)):
        raise HTTPException(status_code=409, detail="이미 선생님 프로필이 등록되어 있습니다.")
    teacher = Teacher(academy_id=tenant_id, user_id=linked_user.id, name=(payload.name or linked_user.name).strip(), phone=payload.phone)
    db.add(teacher)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="선생님 계정 또는 프로필이 이미 등록되어 있습니다.") from None
    db.refresh(teacher)
    return _teacher_read(teacher, linked_user.email)


@router.patch("/teachers/{teacher_id}", response_model=TeacherRead)
def update_teacher(
    teacher_id: uuid.UUID,
    payload: TeacherUpdate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="선생님을 찾을 수 없습니다.")
    if actor.role == UserRole.TEACHER:
        if teacher.user_id != actor.id or "employment_status" in payload.model_fields_set:
            raise HTTPException(status_code=403, detail="본인 프로필 정보만 수정할 수 있습니다.")
    elif actor.role not in admin_roles or (actor.role == UserRole.ACADEMY_ADMIN and actor.academy_id != teacher.academy_id):
        raise HTTPException(status_code=404, detail="선생님을 찾을 수 없습니다.")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("name") is None and "name" in changes:
        raise HTTPException(status_code=422, detail="이름을 비워 둘 수 없습니다.")
    for field, value in changes.items():
        setattr(teacher, field, value.strip() if field == "name" else value)
    db.commit()
    db.refresh(teacher)
    email = db.scalar(select(User.email).where(User.id == teacher.user_id))
    return _teacher_read(teacher, email)


@router.get("/students", response_model=list[StudentRead])
def list_students(
    academy_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Student]:
    academy_scope = read_academy_filter(user, academy_id)
    query = select(Student).order_by(Student.name).limit(limit).offset(offset)
    if academy_scope:
        query = query.where(Student.academy_id == academy_scope)
    if user.role == UserRole.STUDENT:
        query = query.where(Student.user_id == user.id)
    elif user.role == UserRole.TEACHER:
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
        if teacher is None:
            return []
        from app.models.course import Course
        from app.models.enrollment import Enrollment
        query = query.join(Enrollment, (Enrollment.student_id == Student.id) & (Enrollment.academy_id == Student.academy_id)).join(
            Course, (Course.id == Enrollment.course_id) & (Course.academy_id == Enrollment.academy_id)
        ).where(Course.teacher_id == teacher.id).distinct()
    if search:
        query = query.where(Student.name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query).all())


@router.post("/students", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> Student:
    tenant_id = write_academy_id(actor, academy_id)
    email = str(payload.email).lower() if payload.email else None
    linked_user = db.get(User, payload.user_id) if payload.user_id else None
    if payload.user_id and (linked_user is None or linked_user.role != UserRole.STUDENT or linked_user.academy_id != tenant_id):
        raise HTTPException(status_code=422, detail="같은 학원의 학생 계정을 선택해 주세요.")
    if payload.password:
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
        linked_user = User(academy_id=tenant_id, email=email, name=payload.name.strip(), role=UserRole.STUDENT, password_hash=hash_password(payload.password))
        db.add(linked_user)
        db.flush()
    if linked_user and db.scalar(select(Student.id).where(Student.user_id == linked_user.id)):
        raise HTTPException(status_code=409, detail="이미 학생 프로필이 연결되어 있습니다.")
    academy = db.get(Academy, tenant_id)
    if academy is None:
        raise HTTPException(status_code=404, detail="학원을 찾을 수 없습니다.")
    if academy.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="이용 중지된 학원에는 학생을 등록할 수 없습니다.")
    values = payload.model_dump(exclude={"email", "password"})
    values["user_id"] = linked_user.id if linked_user else None
    student = Student(academy_id=tenant_id, **values, email=email or (linked_user.email if linked_user else None))
    db.add(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="학생 계정 또는 프로필이 이미 등록되어 있습니다.") from None
    db.refresh(student)
    return student


@router.patch("/students/{student_id}", response_model=StudentRead)
def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> Student:
    query = select(Student).where(Student.id == student_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        query = query.where(Student.academy_id == actor.academy_id)
    student = db.scalar(query)
    if student is None:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("name") is None and "name" in changes:
        raise HTTPException(status_code=422, detail="이름을 비워 둘 수 없습니다.")
    for field, value in changes.items():
        setattr(student, field, value.strip() if field == "name" else (str(value).lower() if field == "email" and value else value))
    db.commit()
    db.refresh(student)
    return student
