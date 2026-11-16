import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.academy import Academy
from app.models.user import User, UserRole


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, TestSession
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def add_user(session_factory, email: str, role: UserRole, academy_id: uuid.UUID | None, password: str = "local-test-password-123") -> User:
    with session_factory.begin() as session:
        user = User(
            email=email,
            name=email.split("@")[0],
            role=role,
            academy_id=academy_id,
            password_hash=hash_password(password),
        )
        session.add(user)
        session.flush()
        return user


@pytest.fixture
def accounts(client):
    test_client, session_factory = client
    with session_factory.begin() as session:
        academy_a = Academy(name="학원 A", code="academy-a")
        academy_b = Academy(name="학원 B", code="academy-b")
        session.add_all([academy_a, academy_b])
        session.flush()
        academy_a_id, academy_b_id = academy_a.id, academy_b.id
    admin = add_user(session_factory, "admin@example.com", UserRole.ACADEMY_ADMIN, academy_a_id)
    add_user(session_factory, "teacher-a@example.com", UserRole.TEACHER, academy_a_id)
    add_user(session_factory, "teacher-b@example.com", UserRole.TEACHER, academy_b_id)
    add_user(session_factory, "platform@example.com", UserRole.SUPER_ADMIN, None)
    return test_client, admin, academy_a_id, academy_b_id


def login(client: TestClient, email: str, password: str = "local-test-password-123") -> None:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()


def test_login_session_and_logout(accounts):
    client, admin, academy_a_id, _ = accounts
    login(client, "admin@example.com")
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == str(admin.id)
    assert me.json()["academy_id"] == str(academy_a_id)

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_rejects_invalid_credentials(accounts):
    client, *_ = accounts
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_academy_admin_user_list_and_create_stay_in_tenant(accounts):
    client, _, academy_a_id, academy_b_id = accounts
    login(client, "admin@example.com")

    listed = client.get(f"/api/v1/users?academy_id={academy_b_id}")
    assert listed.status_code == 200
    assert {user["email"] for user in listed.json()} == {"admin@example.com", "teacher-a@example.com"}

    created = client.post("/api/v1/users", json={
        "email": "new-teacher@example.com",
        "password": "another-test-password-123",
        "name": "새 선생님",
        "role": "TEACHER",
        "academy_id": str(academy_b_id),
    })
    assert created.status_code == 201
    assert created.json()["academy_id"] == str(academy_a_id)


def test_non_admin_cannot_manage_users(accounts):
    client, *_ = accounts
    login(client, "teacher-a@example.com")
    assert client.post("/api/v1/users", json={
        "email": "student@example.com",
        "password": "another-test-password-123",
        "name": "학생",
        "role": "STUDENT",
    }).status_code == 403


def test_platform_admin_can_list_academies(accounts):
    client, *_ = accounts
    login(client, "platform@example.com")
    response = client.get("/api/v1/academies")
    assert response.status_code == 200
    assert {academy["code"] for academy in response.json()} == {"academy-a", "academy-b"}


def test_academy_admin_cannot_manage_platform_academies(accounts):
    client, *_ = accounts
    login(client, "admin@example.com")
    assert client.get("/api/v1/academies").status_code == 403


def create_login_account(client: TestClient, role: str, email: str, name: str) -> dict:
    response = client.post("/api/v1/users", json={
        "email": email,
        "password": "another-test-password-123",
        "name": name,
        "role": role,
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_student_profile_is_tenant_scoped_and_private(accounts):
    client, _, academy_a_id, academy_b_id = accounts
    login(client, "admin@example.com")
    student_user = create_login_account(client, "STUDENT", "new-student@example.com", "새 학생")
    student = client.post("/api/v1/students", json={
        "user_id": student_user["id"],
        "name": "새 학생",
        "email": student_user["email"],
        "guardian_name": "보호자",
    })
    assert student.status_code == 201, student.text

    assert client.post(f"/api/v1/students?academy_id={academy_b_id}", json={"name": "다른 학원 학생"}).status_code == 403

    login(client, "new-student@example.com", "another-test-password-123")
    own_profile = client.get("/api/v1/students")
    assert own_profile.status_code == 200
    assert [row["id"] for row in own_profile.json()] == [student.json()["id"]]
    assert client.get(f"/api/v1/students?academy_id={academy_b_id}").status_code == 403


def test_course_enrollment_and_teacher_student_visibility(accounts):
    client, _, academy_a_id, _ = accounts
    login(client, "admin@example.com")
    teacher = client.post("/api/v1/teachers", json={
        "email": "new-teacher@example.com",
        "password": "another-test-password-123",
        "name": "새 선생님",
    })
    assert teacher.status_code == 201, teacher.text
    student = client.post("/api/v1/students", json={
        "email": "course-student@example.com",
        "password": "another-test-password-123",
        "name": "수강 학생",
    })
    assert student.status_code == 201, student.text
    subject = client.post("/api/v1/subjects", json={"name": "수학", "color": "#123ABC"})
    assert subject.status_code == 201, subject.text
    course = client.post("/api/v1/courses", json={
        "subject_id": subject.json()["id"],
        "teacher_id": teacher.json()["id"],
        "name": "중등 수학",
    })
    assert course.status_code == 201, course.text
    enrollment_body = {
        "course_id": course.json()["id"],
        "student_id": student.json()["id"],
        "start_date": "2026-11-01",
    }
    enrollment = client.post("/api/v1/enrollments", json=enrollment_body)
    assert enrollment.status_code == 201, enrollment.text
    assert client.post("/api/v1/enrollments", json=enrollment_body).status_code == 409

    login(client, "new-teacher@example.com", "another-test-password-123")
    assert [row["id"] for row in client.get("/api/v1/courses").json()] == [course.json()["id"]]
    assert [row["id"] for row in client.get("/api/v1/students").json()] == [student.json()["id"]]
    assert [row["id"] for row in client.get("/api/v1/enrollments").json()] == [enrollment.json()["id"]]


def test_schedule_overlap_generation_attendance_and_session_visibility(accounts):
    client, _, _, _ = accounts
    login(client, "admin@example.com")
    teacher_user = create_login_account(client, "TEACHER", "schedule-teacher@example.com", "시간표 선생님")
    teacher = client.post("/api/v1/teachers", json={"user_id": teacher_user["id"]})
    student_user = create_login_account(client, "STUDENT", "schedule-student@example.com", "시간표 학생")
    student = client.post("/api/v1/students", json={"user_id": student_user["id"], "name": "시간표 학생"})
    subject = client.post("/api/v1/subjects", json={"name": "과학"})
    course = client.post("/api/v1/courses", json={
        "subject_id": subject.json()["id"], "teacher_id": teacher.json()["id"], "name": "과학 탐구",
    })
    enrollment = client.post("/api/v1/enrollments", json={
        "course_id": course.json()["id"], "student_id": student.json()["id"], "start_date": "2026-11-01",
    })
    assert enrollment.status_code == 201
    schedule_body = {
        "course_id": course.json()["id"], "teacher_id": teacher.json()["id"],
        "day_of_week": 0, "start_time": "15:00", "end_time": "16:00",
        "effective_start_date": "2026-11-16", "room": "201호",
    }
    schedule = client.post("/api/v1/schedules", json=schedule_body)
    assert schedule.status_code == 201, schedule.text
    overlap = client.post("/api/v1/schedules", json={**schedule_body, "start_time": "15:30", "end_time": "16:30"})
    assert overlap.status_code == 409

    generation_body = {"start_date": "2026-11-16", "end_date": "2026-11-22"}
    generated = client.post("/api/v1/lesson-sessions/generate", json=generation_body)
    assert generated.status_code == 200, generated.text
    assert generated.json()["created"] == 1
    assert client.post("/api/v1/lesson-sessions/generate", json=generation_body).json()["created"] == 0
    sessions = client.get("/api/v1/lesson-sessions?start_date=2026-11-16&end_date=2026-11-22")
    assert len(sessions.json()) == 1
    session = sessions.json()[0]
    assert session["participant_count"] == 1

    login(client, "schedule-teacher@example.com", "another-test-password-123")
    attendance = client.patch(f"/api/v1/lesson-sessions/{session['id']}/students/{student.json()['id']}", json={"attendance_status": "PRESENT"})
    assert attendance.status_code == 200, attendance.text
    assert attendance.json()["attendance_status"] == "PRESENT"
    assert client.patch(f"/api/v1/lesson-sessions/{session['id']}/status", json={"status": "IN_PROGRESS"}).status_code == 200
    assert client.patch(f"/api/v1/lesson-sessions/{session['id']}/status", json={"status": "COMPLETED"}).status_code == 200

    login(client, "schedule-student@example.com", "another-test-password-123")
    own_sessions = client.get("/api/v1/lesson-sessions?start_date=2026-11-16&end_date=2026-11-22")
    assert [row["id"] for row in own_sessions.json()] == [session["id"]]
