import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson_session import LessonSession, LessonSessionStudent
from app.models.schedule import Schedule
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.permissions.auth import get_current_user, require_roles
from app.schemas.schedule import (
    AttendanceUpdate, GenerateSessionsRequest, LessonSessionRead, LessonSessionStudentRead,
    ScheduleCreate, ScheduleRead, ScheduleUpdate, SessionStatusUpdate,
)
from app.services.tenancy import read_academy_filter, write_academy_id

router = APIRouter(tags=["schedules and sessions"])
admin_roles = (UserRole.SUPER_ADMIN, UserRole.ACADEMY_ADMIN)
weekday_names = ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")


def _schedule_query():
    return select(Schedule, Course.name, Teacher.name, Subject.name).join(
        Course, (Course.id == Schedule.course_id) & (Course.academy_id == Schedule.academy_id)
    ).join(Teacher, (Teacher.id == Schedule.teacher_id) & (Teacher.academy_id == Schedule.academy_id)).join(
        Subject, (Subject.id == Course.subject_id) & (Subject.academy_id == Course.academy_id)
    )


def _schedule_read(schedule: Schedule, course_name: str, teacher_name: str, subject_name: str) -> dict:
    return {"id": schedule.id, "academy_id": schedule.academy_id, "course_id": schedule.course_id,
            "teacher_id": schedule.teacher_id, "day_of_week": schedule.day_of_week,
            "start_time": schedule.start_time, "end_time": schedule.end_time,
            "effective_start_date": schedule.effective_start_date, "effective_end_date": schedule.effective_end_date,
            "room": schedule.room, "status": schedule.status, "course_name": course_name,
            "teacher_name": teacher_name, "subject_name": subject_name}


def _session_query():
    participants = select(
        LessonSessionStudent.lesson_session_id.label("session_id"),
        func.count(LessonSessionStudent.id).label("participant_count"),
    ).group_by(LessonSessionStudent.lesson_session_id).subquery()
    return select(
        LessonSession, Course.name, Teacher.name, Subject.name, func.coalesce(participants.c.participant_count, 0)
    ).join(Course, (Course.id == LessonSession.course_id) & (Course.academy_id == LessonSession.academy_id)).join(
        Teacher, (Teacher.id == LessonSession.teacher_id) & (Teacher.academy_id == LessonSession.academy_id)
    ).join(Subject, (Subject.id == Course.subject_id) & (Subject.academy_id == Course.academy_id)).outerjoin(
        participants, participants.c.session_id == LessonSession.id
    )


def _session_read(session: LessonSession, course_name: str, teacher_name: str, subject_name: str, count: int) -> dict:
    return {"id": session.id, "academy_id": session.academy_id, "course_id": session.course_id,
            "teacher_id": session.teacher_id, "schedule_id": session.schedule_id,
            "scheduled_at": session.scheduled_at, "started_at": session.started_at, "ended_at": session.ended_at,
            "status": session.status, "room": session.room, "course_name": course_name,
            "teacher_name": teacher_name, "subject_name": subject_name, "participant_count": count}


def _validate_teacher_overlap(db: Session, teacher_id: uuid.UUID, day: int, start_time: time, end_time: time,
                              start_date: date, end_date: date | None, skip_id: uuid.UUID | None = None) -> None:
    # Lock the teacher row while checking and inserting so simultaneous schedule edits cannot race.
    if db.scalar(select(Teacher.id).where(Teacher.id == teacher_id).with_for_update()) is None:
        raise HTTPException(status_code=404, detail="선생님을 찾을 수 없습니다.")
    existing_rules = db.scalars(select(Schedule).where(
        Schedule.teacher_id == teacher_id,
        Schedule.day_of_week == day,
        Schedule.status == "ACTIVE",
        Schedule.id != skip_id if skip_id else True,
    )).all()
    for existing in existing_rules:
        effective_dates_overlap = (end_date is None or existing.effective_start_date <= end_date) and (
            existing.effective_end_date is None or existing.effective_end_date >= start_date
        )
        time_overlaps = start_time < existing.end_time and existing.start_time < end_time
        if effective_dates_overlap and time_overlaps:
            raise HTTPException(status_code=409, detail=f"선생님의 {weekday_names[day]} {existing.start_time:%H:%M}–{existing.end_time:%H:%M} 시간표와 겹칩니다.")


@router.get("/schedules", response_model=list[ScheduleRead])
def list_schedules(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    academy_id: uuid.UUID | None = Query(default=None),
    teacher_id: uuid.UUID | None = Query(default=None),
    course_id: uuid.UUID | None = Query(default=None),
    include_cancelled: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    local_today = datetime.now(ZoneInfo(settings.timezone)).date()
    start_date = start_date or local_today - timedelta(days=local_today.weekday())
    end_date = end_date or start_date + timedelta(days=6)
    if end_date < start_date or (end_date - start_date).days > 31:
        raise HTTPException(status_code=422, detail="조회 기간은 최대 32일로 설정해 주세요.")
    scope = read_academy_filter(actor, academy_id)
    query = _schedule_query().order_by(Schedule.day_of_week, Schedule.start_time).limit(limit).offset(offset)
    if scope:
        query = query.where(Schedule.academy_id == scope)
    if not include_cancelled:
        query = query.where(Schedule.status == "ACTIVE")
    query = query.where(Schedule.effective_start_date <= end_date).where(
        (Schedule.effective_end_date.is_(None)) | (Schedule.effective_end_date >= start_date)
    )
    if actor.role == UserRole.TEACHER:
        teacher = db.scalar(select(Teacher.id).where(Teacher.user_id == actor.id))
        if teacher is None:
            return []
        query = query.where(Schedule.teacher_id == teacher)
    elif actor.role == UserRole.STUDENT:
        student = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        if student is None:
            return []
        query = query.join(Enrollment, (Enrollment.course_id == Schedule.course_id) & (Enrollment.academy_id == Schedule.academy_id)).where(
            Enrollment.student_id == student, Enrollment.status == "ACTIVE"
        )
    if teacher_id:
        query = query.where(Schedule.teacher_id == teacher_id)
    if course_id:
        query = query.where(Schedule.course_id == course_id)
    return [_schedule_read(*row) for row in db.execute(query).unique().all()]


@router.post("/schedules", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict:
    tenant_id = write_academy_id(actor, academy_id)
    course = db.scalar(select(Course).where(Course.id == payload.course_id, Course.academy_id == tenant_id, Course.status == "ACTIVE"))
    if course is None:
        raise HTTPException(status_code=422, detail="같은 학원의 운영 중인 수업을 선택해 주세요.")
    teacher_id = payload.teacher_id or course.teacher_id
    teacher = db.scalar(select(Teacher).where(Teacher.id == teacher_id, Teacher.academy_id == tenant_id, Teacher.employment_status == "ACTIVE"))
    if teacher is None:
        raise HTTPException(status_code=422, detail="같은 학원의 재직 중인 선생님을 선택해 주세요.")
    _validate_teacher_overlap(db, teacher.id, payload.day_of_week, payload.start_time, payload.end_time,
                             payload.effective_start_date, payload.effective_end_date)
    schedule = Schedule(academy_id=tenant_id, teacher_id=teacher.id, **payload.model_dump(exclude={"teacher_id"}))
    db.add(schedule)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="시간표가 다른 일정과 겹칩니다.") from None
    db.refresh(schedule)
    return _schedule_read(schedule, course.name, teacher.name, db.get(Subject, course.subject_id).name)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleRead)
def update_schedule(
    schedule_id: uuid.UUID,
    payload: ScheduleUpdate,
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict:
    query = select(Schedule).where(Schedule.id == schedule_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        query = query.where(Schedule.academy_id == actor.academy_id)
    schedule = db.scalar(query)
    if schedule is None:
        raise HTTPException(status_code=404, detail="시간표를 찾을 수 없습니다.")
    changes = payload.model_dump(exclude_unset=True)
    course_id = changes.get("course_id", schedule.course_id)
    teacher_id = changes.get("teacher_id", schedule.teacher_id)
    course = db.scalar(select(Course).where(Course.id == course_id, Course.academy_id == schedule.academy_id))
    teacher = db.scalar(select(Teacher).where(Teacher.id == teacher_id, Teacher.academy_id == schedule.academy_id))
    if course is None or teacher is None:
        raise HTTPException(status_code=422, detail="같은 학원의 수업과 선생님만 지정할 수 있습니다.")
    day = changes.get("day_of_week", schedule.day_of_week)
    start = changes.get("start_time", schedule.start_time)
    end = changes.get("end_time", schedule.end_time)
    effective_start = changes.get("effective_start_date", schedule.effective_start_date)
    effective_end = changes.get("effective_end_date", schedule.effective_end_date)
    if start >= end or (effective_end is not None and effective_end < effective_start):
        raise HTTPException(status_code=422, detail="시간표 날짜 또는 시간 범위를 확인해 주세요.")
    if changes.get("status", schedule.status) == "ACTIVE":
        _validate_teacher_overlap(db, teacher.id, day, start, end, effective_start, effective_end, skip_id=schedule.id)
    for field, value in changes.items():
        setattr(schedule, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="시간표가 다른 일정과 겹칩니다.") from None
    db.refresh(schedule)
    subject = db.get(Subject, course.subject_id)
    return _schedule_read(schedule, course.name, teacher.name, subject.name)


@router.post("/lesson-sessions/generate")
def generate_sessions(
    payload: GenerateSessionsRequest,
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    tenant_id = write_academy_id(actor, academy_id)
    schedules = db.scalars(select(Schedule).where(
        Schedule.academy_id == tenant_id,
        Schedule.status == "ACTIVE",
        Schedule.effective_start_date <= payload.end_date,
        (Schedule.effective_end_date.is_(None)) | (Schedule.effective_end_date >= payload.start_date),
    ).order_by(Schedule.id).with_for_update()).all()
    created = 0
    tz = ZoneInfo(settings.timezone)
    current_date = payload.start_date
    while current_date <= payload.end_date:
        for schedule in schedules:
            if current_date.weekday() != schedule.day_of_week:
                continue
            if current_date < schedule.effective_start_date or (schedule.effective_end_date and current_date > schedule.effective_end_date):
                continue
            local_datetime = datetime.combine(current_date, schedule.start_time, tzinfo=tz)
            scheduled_at = local_datetime.astimezone(timezone.utc)
            if db.scalar(select(LessonSession.id).where(LessonSession.schedule_id == schedule.id, LessonSession.scheduled_at == scheduled_at)):
                continue
            session = LessonSession(academy_id=tenant_id, course_id=schedule.course_id, teacher_id=schedule.teacher_id,
                                    schedule_id=schedule.id, scheduled_at=scheduled_at, room=schedule.room)
            db.add(session)
            db.flush()
            enrollments = db.scalars(select(Enrollment).where(
                Enrollment.academy_id == tenant_id, Enrollment.course_id == schedule.course_id,
                Enrollment.status == "ACTIVE", Enrollment.start_date <= current_date,
                (Enrollment.end_date.is_(None)) | (Enrollment.end_date >= current_date),
            )).all()
            db.add_all([LessonSessionStudent(academy_id=tenant_id, lesson_session_id=session.id, student_id=e.student_id) for e in enrollments])
            created += 1
        current_date += timedelta(days=1)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="수업 회차 생성 중 일정이 변경되었습니다. 다시 시도해 주세요.") from None
    return {"created": created, "start_date": payload.start_date.isoformat(), "end_date": payload.end_date.isoformat()}


@router.get("/lesson-sessions", response_model=list[LessonSessionRead])
def list_lesson_sessions(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    academy_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(PLANNED|IN_PROGRESS|COMPLETED|CANCELLED)$"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    local_today = datetime.now(ZoneInfo(settings.timezone)).date()
    start_date = start_date or local_today - timedelta(days=local_today.weekday())
    end_date = end_date or start_date + timedelta(days=6)
    if end_date < start_date or (end_date - start_date).days > 31:
        raise HTTPException(status_code=422, detail="조회 기간은 최대 32일로 설정해 주세요.")
    tz = ZoneInfo(settings.timezone)
    start_at = datetime.combine(start_date, time.min, tzinfo=tz).astimezone(timezone.utc)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc)
    scope = read_academy_filter(actor, academy_id)
    query = _session_query().where(LessonSession.scheduled_at >= start_at, LessonSession.scheduled_at < end_at).order_by(LessonSession.scheduled_at).limit(limit).offset(offset)
    if scope:
        query = query.where(LessonSession.academy_id == scope)
    if status_filter:
        query = query.where(LessonSession.status == status_filter)
    if actor.role == UserRole.TEACHER:
        teacher_id = db.scalar(select(Teacher.id).where(Teacher.user_id == actor.id))
        if teacher_id is None:
            return []
        query = query.where(LessonSession.teacher_id == teacher_id)
    elif actor.role == UserRole.STUDENT:
        student_id = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        if student_id is None:
            return []
        query = query.join(LessonSessionStudent, LessonSessionStudent.lesson_session_id == LessonSession.id).where(LessonSessionStudent.student_id == student_id)
    return [_session_read(*row) for row in db.execute(query).unique().all()]


def _visible_session(session_id: uuid.UUID, actor: User, db: Session) -> LessonSession:
    query = select(LessonSession).where(LessonSession.id == session_id)
    if actor.role == UserRole.ACADEMY_ADMIN:
        query = query.where(LessonSession.academy_id == actor.academy_id)
    elif actor.role == UserRole.TEACHER:
        teacher_id = db.scalar(select(Teacher.id).where(Teacher.user_id == actor.id))
        query = query.where(LessonSession.teacher_id == teacher_id)
    elif actor.role == UserRole.STUDENT:
        student_id = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        query = query.join(LessonSessionStudent, LessonSessionStudent.lesson_session_id == LessonSession.id).where(LessonSessionStudent.student_id == student_id)
    session = db.scalar(query)
    if session is None:
        raise HTTPException(status_code=404, detail="수업 회차를 찾을 수 없습니다.")
    return session


@router.get("/lesson-sessions/{session_id}/students", response_model=list[LessonSessionStudentRead])
def list_session_students(
    session_id: uuid.UUID,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    _visible_session(session_id, actor, db)
    query = select(LessonSessionStudent, Student.name).join(
        Student, (Student.id == LessonSessionStudent.student_id) & (Student.academy_id == LessonSessionStudent.academy_id)
    ).where(LessonSessionStudent.lesson_session_id == session_id).order_by(Student.name)
    if actor.role == UserRole.STUDENT:
        student_id = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        query = query.where(LessonSessionStudent.student_id == student_id)
    return [{"id": item.id, "lesson_session_id": item.lesson_session_id, "student_id": item.student_id,
             "student_name": name, "attendance_status": item.attendance_status} for item, name in db.execute(query).all()]


@router.patch("/lesson-sessions/{session_id}/students/{student_id}", response_model=LessonSessionStudentRead)
def update_attendance(
    session_id: uuid.UUID,
    student_id: uuid.UUID,
    payload: AttendanceUpdate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = _visible_session(session_id, actor, db)
    if actor.role not in (*admin_roles, UserRole.TEACHER):
        raise HTTPException(status_code=403, detail="출결을 수정할 권한이 없습니다.")
    if session.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="취소된 수업의 출결은 수정할 수 없습니다.")
    participant = db.scalar(select(LessonSessionStudent).where(
        LessonSessionStudent.lesson_session_id == session.id, LessonSessionStudent.student_id == student_id,
        LessonSessionStudent.academy_id == session.academy_id,
    ))
    if participant is None:
        raise HTTPException(status_code=404, detail="수업 참여 학생을 찾을 수 없습니다.")
    participant.attendance_status = payload.attendance_status
    db.commit()
    db.refresh(participant)
    name = db.scalar(select(Student.name).where(Student.id == student_id, Student.academy_id == session.academy_id))
    return {"id": participant.id, "lesson_session_id": participant.lesson_session_id,
            "student_id": participant.student_id, "student_name": name,
            "attendance_status": participant.attendance_status}


@router.patch("/lesson-sessions/{session_id}/status", response_model=LessonSessionRead)
def update_session_status(
    session_id: uuid.UUID,
    payload: SessionStatusUpdate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = _visible_session(session_id, actor, db)
    if actor.role not in (*admin_roles, UserRole.TEACHER):
        raise HTTPException(status_code=403, detail="수업 상태를 변경할 권한이 없습니다.")
    allowed_transitions = {"PLANNED": {"IN_PROGRESS", "COMPLETED", "CANCELLED"}, "IN_PROGRESS": {"COMPLETED", "CANCELLED"}}
    if payload.status not in allowed_transitions.get(session.status, set()):
        raise HTTPException(status_code=409, detail="현재 수업 상태에서 요청한 변경을 적용할 수 없습니다.")
    now = datetime.now(timezone.utc)
    if payload.status == "IN_PROGRESS":
        session.started_at = now
    elif payload.status == "COMPLETED":
        session.started_at = session.started_at or now
        session.ended_at = now
    session.status = payload.status
    db.commit()
    db.refresh(session)
    row = db.execute(_session_query().where(LessonSession.id == session.id)).one()
    return _session_read(*row)
