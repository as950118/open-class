import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.course import Course
from app.models.lesson_log import LessonLog
from app.models.lesson_session import LessonSession, LessonSessionStudent
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.permissions.auth import get_current_user
from app.schemas.lesson_log import LessonLogCreate, LessonLogRead, LessonLogUpdate
from app.services.tenancy import read_academy_filter

router = APIRouter(tags=["lesson logs"])
admin_roles = (UserRole.SUPER_ADMIN, UserRole.ACADEMY_ADMIN)


def _log_query():
    return select(LessonLog, LessonSession.scheduled_at, Course.id, Course.name, Teacher.name, Student.name, Subject.name).join(
        LessonSession, (LessonSession.id == LessonLog.lesson_session_id) & (LessonSession.academy_id == LessonLog.academy_id)
    ).join(Course, (Course.id == LessonSession.course_id) & (Course.academy_id == LessonSession.academy_id)).join(
        Teacher, (Teacher.id == LessonLog.teacher_id) & (Teacher.academy_id == LessonLog.academy_id)
    ).join(Student, (Student.id == LessonLog.student_id) & (Student.academy_id == LessonLog.academy_id)).join(
        Subject, (Subject.id == Course.subject_id) & (Subject.academy_id == Course.academy_id)
    )


def _read(row) -> dict:
    log, scheduled_at, course_id, course_name, teacher_name, student_name, subject_name = row
    return {"id": log.id, "academy_id": log.academy_id, "lesson_session_id": log.lesson_session_id,
            "teacher_id": log.teacher_id, "student_id": log.student_id, "course_id": course_id,
            "course_name": course_name, "teacher_name": teacher_name, "student_name": student_name,
            "subject_name": subject_name, "subject": log.subject, "lesson_content": log.lesson_content,
            "progress_content": log.progress_content, "understanding_level": log.understanding_level,
            "homework": log.homework, "feedback": log.feedback, "next_plan": log.next_plan,
            "scheduled_at": scheduled_at, "created_at": log.created_at, "updated_at": log.updated_at}


def _visible_log(log_id: uuid.UUID, actor: User, db: Session) -> LessonLog:
    query = select(LessonLog).where(LessonLog.id == log_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        query = query.where(LessonLog.academy_id == actor.academy_id)
    elif actor.role == UserRole.TEACHER:
        query = query.where(LessonLog.teacher_id == select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery())
    elif actor.role == UserRole.STUDENT:
        query = query.where(LessonLog.student_id == select(Student.id).where(Student.user_id == actor.id).scalar_subquery())
    log = db.scalar(query)
    if log is None:
        raise HTTPException(status_code=404, detail="수업 일지를 찾을 수 없습니다.")
    return log


@router.get("/lesson-logs", response_model=list[LessonLogRead])
def list_lesson_logs(
    academy_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    teacher_id: uuid.UUID | None = Query(default=None),
    course_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    if actor.role not in (*admin_roles, UserRole.TEACHER, UserRole.STUDENT):
        raise HTTPException(status_code=403, detail="수업 일지를 조회할 권한이 없습니다.")
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=422, detail="종료일은 시작일보다 빠를 수 없습니다.")
    query = _log_query().order_by(LessonSession.scheduled_at.desc(), LessonLog.created_at.desc())
    academy_scope = read_academy_filter(actor, academy_id)
    if academy_scope:
        query = query.where(LessonLog.academy_id == academy_scope)
    if actor.role == UserRole.TEACHER:
        query = query.where(LessonLog.teacher_id == select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery())
    elif actor.role == UserRole.STUDENT:
        own_student = select(Student.id).where(Student.user_id == actor.id).scalar_subquery()
        query = query.where(LessonLog.student_id == own_student)
    if student_id:
        query = query.where(LessonLog.student_id == student_id)
    if teacher_id:
        query = query.where(LessonLog.teacher_id == teacher_id)
    if course_id:
        query = query.where(LessonSession.course_id == course_id)
    tz = ZoneInfo(settings.timezone)
    if start_date:
        query = query.where(LessonSession.scheduled_at >= datetime.combine(start_date, time.min, tzinfo=tz))
    if end_date:
        query = query.where(LessonSession.scheduled_at < datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=tz))
    if search:
        term = f"%{search.strip()}%"
        query = query.where((LessonLog.subject.ilike(term)) | (LessonLog.lesson_content.ilike(term)) |
                            (LessonLog.progress_content.ilike(term)) | (LessonLog.homework.ilike(term)) |
                            (LessonLog.feedback.ilike(term)) | (LessonLog.next_plan.ilike(term)) |
                            (Student.name.ilike(term)) | (Teacher.name.ilike(term)) |
                            (Course.name.ilike(term)) | (Subject.name.ilike(term)))
    return [_read(row) for row in db.execute(query.limit(limit).offset(offset)).all()]


@router.post("/lesson-logs", response_model=LessonLogRead, status_code=status.HTTP_201_CREATED)
def create_lesson_log(
    payload: LessonLogCreate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if actor.role not in (*admin_roles, UserRole.TEACHER):
        raise HTTPException(status_code=403, detail="수업 일지를 작성할 권한이 없습니다.")
    session_query = select(LessonSession).where(LessonSession.id == payload.lesson_session_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        session_query = session_query.where(LessonSession.academy_id == actor.academy_id)
    elif actor.role == UserRole.TEACHER:
        own_teacher = select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery()
        session_query = session_query.where(LessonSession.teacher_id == own_teacher)
    session = db.scalar(session_query)
    if session is None:
        raise HTTPException(status_code=404, detail="수업 회차를 찾을 수 없습니다.")
    if session.status != "COMPLETED":
        raise HTTPException(status_code=409, detail="완료된 수업의 일지만 작성할 수 있습니다.")
    participant = db.scalar(select(LessonSessionStudent).where(
        LessonSessionStudent.lesson_session_id == session.id,
        LessonSessionStudent.student_id == payload.student_id,
        LessonSessionStudent.academy_id == session.academy_id,
    ))
    if participant is None:
        raise HTTPException(status_code=422, detail="해당 수업에 참여한 학생만 일지를 작성할 수 있습니다.")
    log = LessonLog(academy_id=session.academy_id, lesson_session_id=session.id,
                    teacher_id=session.teacher_id, student_id=payload.student_id,
                    **payload.model_dump(exclude={"lesson_session_id", "student_id"}))
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이 학생과 수업의 일지가 이미 작성되어 있습니다.") from None
    row = db.execute(_log_query().where(LessonLog.id == log.id)).one()
    return _read(row)


@router.patch("/lesson-logs/{log_id}", response_model=LessonLogRead)
def update_lesson_log(
    log_id: uuid.UUID,
    payload: LessonLogUpdate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    log = _visible_log(log_id, actor, db)
    if actor.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="학생은 수업 일지를 수정할 수 없습니다.")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="수정할 내용을 입력해 주세요.")
    for field, value in changes.items():
        setattr(log, field, value)
    db.commit()
    row = db.execute(_log_query().where(LessonLog.id == log.id)).one()
    return _read(row)
