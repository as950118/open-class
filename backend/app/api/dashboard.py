import uuid
from datetime import datetime, time, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson_log import LessonLog
from app.models.lesson_session import LessonSession, LessonSessionStudent
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.permissions.auth import get_current_user
from app.services.tenancy import read_academy_filter
from app.api.lesson_logs import _log_query, _read as _lesson_log_read

router = APIRouter(tags=["dashboard and search"])


def _session_visibility(query, actor: User, db: Session):
    if actor.role == UserRole.TEACHER:
        teacher_id = select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery()
        query = query.where(LessonSession.teacher_id == teacher_id)
    elif actor.role == UserRole.STUDENT:
        student_id = select(Student.id).where(Student.user_id == actor.id).scalar_subquery()
        query = query.join(LessonSessionStudent, LessonSessionStudent.lesson_session_id == LessonSession.id).where(LessonSessionStudent.student_id == student_id)
    return query


@router.get("/dashboard")
def dashboard(
    academy_id: uuid.UUID | None = Query(default=None),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if actor.role == UserRole.SUPER_ADMIN:
        academy_scope = read_academy_filter(actor, academy_id)
    else:
        academy_scope = read_academy_filter(actor, academy_id)
    if actor.role == UserRole.STUDENT:
        student_id = db.scalar(select(Student.id).where(Student.user_id == actor.id))
        if student_id is None:
            raise HTTPException(status_code=404, detail="학생 프로필을 찾을 수 없습니다.")
        total_students, total_teachers = 1, 0
    elif actor.role == UserRole.TEACHER:
        teacher_id = db.scalar(select(Teacher.id).where(Teacher.user_id == actor.id))
        total_students = db.scalar(select(func.count(func.distinct(Enrollment.student_id))).join(
            Course, (Course.id == Enrollment.course_id) & (Course.academy_id == Enrollment.academy_id)
        ).where(Course.teacher_id == teacher_id, Enrollment.status == "ACTIVE")) or 0
        total_teachers = 1 if teacher_id else 0
    else:
        student_count = select(func.count(Student.id))
        teacher_count = select(func.count(Teacher.id))
        if academy_scope:
            student_count = student_count.where(Student.academy_id == academy_scope)
            teacher_count = teacher_count.where(Teacher.academy_id == academy_scope)
        total_students = db.scalar(student_count) or 0
        total_teachers = db.scalar(teacher_count) or 0

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()
    start_at = datetime.combine(today, time.min, tzinfo=tz)
    end_at = start_at + timedelta(days=1)
    sessions_query = select(LessonSession, Course.name, Teacher.name, Subject.name,
        select(func.count(LessonSessionStudent.id)).where(LessonSessionStudent.lesson_session_id == LessonSession.id).scalar_subquery()
    ).join(Course, (Course.id == LessonSession.course_id) & (Course.academy_id == LessonSession.academy_id)).join(
        Teacher, (Teacher.id == LessonSession.teacher_id) & (Teacher.academy_id == LessonSession.academy_id)
    ).join(Subject, (Subject.id == Course.subject_id) & (Subject.academy_id == Course.academy_id)).where(
        LessonSession.scheduled_at >= start_at, LessonSession.scheduled_at < end_at,
        LessonSession.status != "CANCELLED",
    )
    if academy_scope:
        sessions_query = sessions_query.where(LessonSession.academy_id == academy_scope)
    sessions_query = _session_visibility(sessions_query, actor, db)
    today_rows = db.execute(sessions_query.order_by(LessonSession.scheduled_at)).unique().all()
    completed = sum(1 for row in today_rows if row[0].status == "COMPLETED")
    log_count_query = select(func.count(LessonLog.id)).join(LessonSession, LessonSession.id == LessonLog.lesson_session_id).where(
        LessonSession.scheduled_at >= start_at, LessonSession.scheduled_at < end_at
    )
    if academy_scope:
        log_count_query = log_count_query.where(LessonLog.academy_id == academy_scope)
    if actor.role == UserRole.TEACHER:
        log_count_query = log_count_query.where(LessonLog.teacher_id == select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery())
    elif actor.role == UserRole.STUDENT:
        log_count_query = log_count_query.where(LessonLog.student_id == select(Student.id).where(Student.user_id == actor.id).scalar_subquery())
    logs_today = db.scalar(log_count_query) or 0
    missing_query = select(func.count(LessonSessionStudent.id)).join(
        LessonSession, (LessonSession.id == LessonSessionStudent.lesson_session_id) & (LessonSession.academy_id == LessonSessionStudent.academy_id)
    ).outerjoin(LessonLog, (LessonLog.lesson_session_id == LessonSession.id) & (LessonLog.student_id == LessonSessionStudent.student_id)).where(
        LessonSession.scheduled_at >= start_at, LessonSession.scheduled_at < end_at,
        LessonSession.status == "COMPLETED", LessonLog.id.is_(None)
    )
    if academy_scope:
        missing_query = missing_query.where(LessonSession.academy_id == academy_scope)
    if actor.role == UserRole.TEACHER:
        missing_query = missing_query.where(LessonSession.teacher_id == select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery())
    elif actor.role == UserRole.STUDENT:
        missing_query = missing_query.where(LessonSessionStudent.student_id == select(Student.id).where(Student.user_id == actor.id).scalar_subquery())
    missing_logs = db.scalar(missing_query) or 0

    recent_query = _log_query().order_by(LessonSession.scheduled_at.desc(), LessonLog.created_at.desc())
    if academy_scope:
        recent_query = recent_query.where(LessonLog.academy_id == academy_scope)
    if actor.role == UserRole.TEACHER:
        recent_query = recent_query.where(LessonLog.teacher_id == select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery())
    elif actor.role == UserRole.STUDENT:
        recent_query = recent_query.where(LessonLog.student_id == select(Student.id).where(Student.user_id == actor.id).scalar_subquery())
    recent_logs = [_lesson_log_read(row) for row in db.execute(recent_query.limit(5)).all()]
    today_sessions = [{"id": row[0].id, "scheduled_at": row[0].scheduled_at, "status": row[0].status,
        "room": row[0].room, "course_name": row[1], "teacher_name": row[2], "subject_name": row[3], "participant_count": row[4]} for row in today_rows]
    return {"total_students": total_students, "total_teachers": total_teachers,
        "today_scheduled": len(today_rows), "today_completed": completed,
        "today_logs": logs_today, "today_missing_logs": missing_logs,
        "today_sessions": today_sessions, "recent_logs": recent_logs}


@router.get("/search")
def search(
    query_text: str = Query(min_length=2, max_length=100, alias="q"),
    academy_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=10),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, str]]]:
    normalized_query = query_text.strip()
    if len(normalized_query) < 2:
        raise HTTPException(status_code=422, detail="검색어는 두 글자 이상 입력해 주세요.")
    term = f"%{normalized_query}%"
    scope = read_academy_filter(actor, academy_id)
    results: dict[str, list[dict[str, str]]] = {"students": [], "teachers": [], "courses": [], "lesson_logs": []}
    students_q = select(Student).where(Student.name.ilike(term)).order_by(Student.name)
    teachers_q = select(Teacher).where(Teacher.name.ilike(term)).order_by(Teacher.name)
    courses_q = select(Course).where(Course.name.ilike(term)).order_by(Course.name)
    if scope:
        students_q = students_q.where(Student.academy_id == scope)
        teachers_q = teachers_q.where(Teacher.academy_id == scope)
        courses_q = courses_q.where(Course.academy_id == scope)
    if actor.role == UserRole.TEACHER:
        own_teacher = select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery()
        students_q = students_q.join(Enrollment, (Enrollment.student_id == Student.id) & (Enrollment.academy_id == Student.academy_id)).join(
            Course, (Course.id == Enrollment.course_id) & (Course.academy_id == Enrollment.academy_id)
        ).where(Course.teacher_id == own_teacher, Enrollment.status == "ACTIVE")
        teachers_q = teachers_q.where(Teacher.user_id == actor.id)
        courses_q = courses_q.where(Course.teacher_id == own_teacher)
    elif actor.role == UserRole.STUDENT:
        own_student = select(Student.id).where(Student.user_id == actor.id).scalar_subquery()
        students_q = students_q.where(Student.id == own_student)
        teachers_q = teachers_q.join(Course, (Course.teacher_id == Teacher.id) & (Course.academy_id == Teacher.academy_id)).join(
            Enrollment, (Enrollment.course_id == Course.id) & (Enrollment.academy_id == Course.academy_id)
        ).where(Enrollment.student_id == own_student)
        courses_q = courses_q.join(Enrollment, (Enrollment.course_id == Course.id) & (Enrollment.academy_id == Course.academy_id)).where(Enrollment.student_id == own_student)
    results["students"] = [{"id": str(row.id), "title": row.name, "subtitle": "학생", "path": "/students"} for row in db.scalars(students_q.limit(limit)).unique().all()]
    results["teachers"] = [{"id": str(row.id), "title": row.name, "subtitle": "선생님", "path": "/teachers"} for row in db.scalars(teachers_q.limit(limit)).unique().all()]
    results["courses"] = [{"id": str(row.id), "title": row.name, "subtitle": "수업", "path": "/courses"} for row in db.scalars(courses_q.limit(limit)).unique().all()]
    logs_q = _log_query().where((LessonLog.subject.ilike(term)) | (LessonLog.lesson_content.ilike(term)) |
        (LessonLog.progress_content.ilike(term)) | (LessonLog.homework.ilike(term)) | (LessonLog.feedback.ilike(term)) |
        (LessonLog.next_plan.ilike(term)) | (Student.name.ilike(term)) | (Teacher.name.ilike(term)) | (Course.name.ilike(term)))
    if scope:
        logs_q = logs_q.where(LessonLog.academy_id == scope)
    if actor.role == UserRole.TEACHER:
        logs_q = logs_q.where(LessonLog.teacher_id == select(Teacher.id).where(Teacher.user_id == actor.id).scalar_subquery())
    elif actor.role == UserRole.STUDENT:
        logs_q = logs_q.where(LessonLog.student_id == select(Student.id).where(Student.user_id == actor.id).scalar_subquery())
    results["lesson_logs"] = [{"id": str(row[0].id), "title": row[0].subject or row[3], "subtitle": f"{row[5]} · {row[4]}", "path": f"/lesson-logs?search={quote(normalized_query)}"} for row in db.execute(logs_q.order_by(LessonSession.scheduled_at.desc()).limit(limit)).all()]
    return results
