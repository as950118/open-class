import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.permissions.auth import get_current_user, require_roles
from app.schemas.academy_data import (
    CourseCreate, CourseRead, CourseUpdate, EnrollmentCreate, EnrollmentRead,
    SubjectCreate, SubjectRead, SubjectUpdate,
)
from app.services.tenancy import read_academy_filter, write_academy_id

router = APIRouter(tags=["courses and enrollment"])
admin_roles = (UserRole.SUPER_ADMIN, UserRole.ACADEMY_ADMIN)


def _course_query():
    return select(Course, Subject.name, Teacher.name).join(
        Subject, (Subject.id == Course.subject_id) & (Subject.academy_id == Course.academy_id)
    ).join(Teacher, (Teacher.id == Course.teacher_id) & (Teacher.academy_id == Course.academy_id))


def _course_read(course: Course, subject_name: str, teacher_name: str) -> dict:
    return {
        "id": course.id, "academy_id": course.academy_id, "subject_id": course.subject_id,
        "teacher_id": course.teacher_id, "name": course.name, "description": course.description,
        "status": course.status, "subject_name": subject_name, "teacher_name": teacher_name,
    }


def _get_course_read(db: Session, course_id: uuid.UUID) -> dict:
    row = db.execute(_course_query().where(Course.id == course_id)).one()
    return _course_read(*row)


@router.get("/subjects", response_model=list[SubjectRead])
def list_subjects(
    academy_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Subject]:
    if actor.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="과목 목록을 조회할 권한이 없습니다.")
    scope = read_academy_filter(actor, academy_id)
    query = select(Subject).order_by(Subject.name).limit(limit).offset(offset)
    if scope:
        query = query.where(Subject.academy_id == scope)
    return list(db.scalars(query).all())


@router.post("/subjects", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> Subject:
    tenant_id = write_academy_id(actor, academy_id)
    subject = Subject(academy_id=tenant_id, **payload.model_dump())
    db.add(subject)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 등록된 과목 이름입니다.") from None
    db.refresh(subject)
    return subject


@router.patch("/subjects/{subject_id}", response_model=SubjectRead)
def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> Subject:
    query = select(Subject).where(Subject.id == subject_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        query = query.where(Subject.academy_id == actor.academy_id)
    subject = db.scalar(query)
    if subject is None:
        raise HTTPException(status_code=404, detail="과목을 찾을 수 없습니다.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None and field == "name":
            raise HTTPException(status_code=422, detail="과목 이름을 비워 둘 수 없습니다.")
        setattr(subject, field, value.strip() if field == "name" and value else value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 등록된 과목 이름입니다.") from None
    db.refresh(subject)
    return subject


@router.get("/courses", response_model=list[CourseRead])
def list_courses(
    academy_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    scope = read_academy_filter(actor, academy_id)
    query = _course_query().order_by(Course.name).limit(limit).offset(offset)
    if scope:
        query = query.where(Course.academy_id == scope)
    if actor.role == UserRole.TEACHER:
        teacher_id = db.scalar(select(Teacher.id).where(Teacher.user_id == actor.id))
        if teacher_id is None:
            return []
        query = query.where(Course.teacher_id == teacher_id)
    elif actor.role == UserRole.STUDENT:
        student_id = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        if student_id is None:
            return []
        query = query.join(Enrollment, (Enrollment.course_id == Course.id) & (Enrollment.academy_id == Course.academy_id)).where(Enrollment.student_id == student_id)
    if search:
        query = query.where(Course.name.ilike(f"%{search.strip()}%"))
    return [_course_read(*row) for row in db.execute(query).unique().all()]


@router.post("/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict:
    tenant_id = write_academy_id(actor, academy_id)
    subject = db.scalar(select(Subject).where(Subject.id == payload.subject_id, Subject.academy_id == tenant_id))
    teacher = db.scalar(select(Teacher).where(Teacher.id == payload.teacher_id, Teacher.academy_id == tenant_id, Teacher.employment_status == "ACTIVE"))
    if subject is None or teacher is None:
        raise HTTPException(status_code=422, detail="같은 학원의 과목과 재직 중인 선생님을 선택해 주세요.")
    course = Course(academy_id=tenant_id, **payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return _course_read(course, subject.name, teacher.name)


@router.patch("/courses/{course_id}", response_model=CourseRead)
def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict:
    query = select(Course).where(Course.id == course_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        query = query.where(Course.academy_id == actor.academy_id)
    course = db.scalar(query)
    if course is None:
        raise HTTPException(status_code=404, detail="수업을 찾을 수 없습니다.")
    changes = payload.model_dump(exclude_unset=True)
    subject_id = changes.get("subject_id", course.subject_id)
    teacher_id = changes.get("teacher_id", course.teacher_id)
    subject = db.scalar(select(Subject).where(Subject.id == subject_id, Subject.academy_id == course.academy_id))
    teacher = db.scalar(select(Teacher).where(Teacher.id == teacher_id, Teacher.academy_id == course.academy_id))
    if subject is None or teacher is None:
        raise HTTPException(status_code=422, detail="같은 학원의 과목과 선생님만 지정할 수 있습니다.")
    for field, value in changes.items():
        if value is None and field == "name":
            raise HTTPException(status_code=422, detail="수업 이름을 비워 둘 수 없습니다.")
        setattr(course, field, value.strip() if field == "name" and value else value)
    db.commit()
    db.refresh(course)
    return _course_read(course, subject.name, teacher.name)


@router.get("/enrollments", response_model=list[EnrollmentRead])
def list_enrollments(
    academy_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    scope = read_academy_filter(actor, academy_id)
    query = select(Enrollment, Course.name, Student.name).join(
        Course, (Course.id == Enrollment.course_id) & (Course.academy_id == Enrollment.academy_id)
    ).join(Student, (Student.id == Enrollment.student_id) & (Student.academy_id == Enrollment.academy_id)).order_by(Enrollment.start_date.desc()).limit(limit).offset(offset)
    if scope:
        query = query.where(Enrollment.academy_id == scope)
    if actor.role == UserRole.TEACHER:
        teacher_id = db.scalar(select(Teacher.id).where(Teacher.user_id == actor.id))
        if teacher_id is None:
            return []
        query = query.where(Course.teacher_id == teacher_id)
    elif actor.role == UserRole.STUDENT:
        student_id = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        if student_id is None:
            return []
        query = query.where(Enrollment.student_id == student_id)
    return [{"id": e.id, "academy_id": e.academy_id, "course_id": e.course_id, "student_id": e.student_id,
             "start_date": e.start_date, "end_date": e.end_date, "status": e.status,
             "course_name": course_name, "student_name": student_name}
            for e, course_name, student_name in db.execute(query).all()]


@router.post("/enrollments", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    payload: EnrollmentCreate,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict:
    tenant_id = write_academy_id(actor, academy_id)
    course = db.scalar(select(Course).where(Course.id == payload.course_id, Course.academy_id == tenant_id, Course.status == "ACTIVE"))
    student = db.scalar(select(Student).where(Student.id == payload.student_id, Student.academy_id == tenant_id, Student.status == "ACTIVE"))
    if course is None or student is None:
        raise HTTPException(status_code=422, detail="같은 학원의 운영 중인 수업과 재원 중인 학생을 선택해 주세요.")
    if db.scalar(select(Enrollment.id).where(Enrollment.course_id == course.id, Enrollment.student_id == student.id)):
        raise HTTPException(status_code=409, detail="학생이 이미 이 수업에 등록되어 있습니다.")
    enrollment = Enrollment(academy_id=tenant_id, **payload.model_dump())
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="학생이 이미 이 수업에 등록되어 있습니다.") from None
    db.refresh(enrollment)
    return {"id": enrollment.id, "academy_id": enrollment.academy_id, "course_id": enrollment.course_id,
            "student_id": enrollment.student_id, "start_date": enrollment.start_date, "end_date": enrollment.end_date,
            "status": enrollment.status, "course_name": course.name, "student_name": student.name}
