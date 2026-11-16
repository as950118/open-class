from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.academy import Academy
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User, UserRole


def seed() -> None:
    if not settings.seed_password or len(settings.seed_password) < 12:
        raise SystemExit("SEED_PASSWORD 환경 변수에 12자 이상의 개발용 비밀번호를 설정해 주세요.")

    with SessionLocal.begin() as db:
        academy = db.scalar(select(Academy).where(Academy.code == "open-class-demo"))
        if academy is None:
            academy = Academy(name="오픈클래스 데모 학원", code="open-class-demo")
            db.add(academy)
            db.flush()

        accounts = [
            ("admin@open-class.example.com", "김민지", UserRole.ACADEMY_ADMIN, academy.id),
            ("teacher@open-class.example.com", "이서준", UserRole.TEACHER, academy.id),
            ("student@open-class.example.com", "김서연", UserRole.STUDENT, academy.id),
            ("platform@open-class.example.com", "플랫폼 관리자", UserRole.SUPER_ADMIN, None),
        ]
        for email, name, role, academy_id in accounts:
            if db.scalar(select(User.id).where(User.email == email)) is None:
                db.add(User(email=email, name=name, role=role, academy_id=academy_id, password_hash=hash_password(settings.seed_password)))
        db.flush()

        teacher_user = db.scalar(select(User).where(User.email == "teacher@open-class.example.com"))
        student_user = db.scalar(select(User).where(User.email == "student@open-class.example.com"))
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id))
        if teacher is None:
            teacher = Teacher(academy_id=academy.id, user_id=teacher_user.id, name=teacher_user.name)
            db.add(teacher)
            db.flush()
        student = db.scalar(select(Student).where(Student.user_id == student_user.id))
        if student is None:
            student = Student(academy_id=academy.id, user_id=student_user.id, name=student_user.name, email=student_user.email)
            db.add(student)
            db.flush()

        subject = db.scalar(select(Subject).where(Subject.academy_id == academy.id, Subject.name == "수학"))
        if subject is None:
            subject = Subject(academy_id=academy.id, name="수학", description="수학 과목 예시", color="#6474E8")
            db.add(subject)
            db.flush()
        course = db.scalar(select(Course).where(Course.academy_id == academy.id, Course.name == "중등 수학 기본반"))
        if course is None:
            course = Course(academy_id=academy.id, subject_id=subject.id, teacher_id=teacher.id, name="중등 수학 기본반")
            db.add(course)
            db.flush()
        if db.scalar(select(Enrollment.id).where(Enrollment.academy_id == academy.id, Enrollment.course_id == course.id, Enrollment.student_id == student.id)) is None:
            start_date = datetime.now(ZoneInfo(settings.timezone)).date()
            db.add(Enrollment(academy_id=academy.id, course_id=course.id, student_id=student.id, start_date=start_date))

    print("개발용 학원, 사용자, 과목, 수업 및 수강 등록이 준비되었습니다. 비밀번호는 SEED_PASSWORD 환경 변수에 설정한 값입니다.")


if __name__ == "__main__":
    seed()
