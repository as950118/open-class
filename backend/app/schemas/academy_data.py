import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class TeacherCreate(BaseModel):
    user_id: uuid.UUID | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12, max_length=200)
    name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def validate_account_source(self):
        if self.user_id is None and (self.email is None or self.password is None or not self.name or not self.name.strip()):
            raise ValueError("선생님 계정을 만들려면 이름, 이메일, 12자 이상의 비밀번호가 필요합니다.")
        if self.user_id is not None and (self.email is not None or self.password is not None):
            raise ValueError("기존 계정을 연결할 때 이메일과 비밀번호는 입력할 수 없습니다.")
        return self


class TeacherUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    employment_status: Literal["ACTIVE", "ON_LEAVE", "RESIGNED"] | None = None


class TeacherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    name: str
    phone: str | None
    employment_status: str


class StudentCreate(BaseModel):
    user_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12, max_length=200)
    birth_date: date | None = None
    guardian_name: str | None = Field(default=None, max_length=100)
    guardian_phone: str | None = Field(default=None, max_length=30)
    memo: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("학생 이름을 입력해 주세요.")
        return value

    @model_validator(mode="after")
    def validate_optional_account(self):
        if self.password is not None and (self.email is None or self.user_id is not None):
            raise ValueError("학생 계정을 만들려면 이메일이 필요하며 기존 계정 ID와 함께 입력할 수 없습니다.")
        return self


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    birth_date: date | None = None
    guardian_name: str | None = Field(default=None, max_length=100)
    guardian_phone: str | None = Field(default=None, max_length=30)
    status: Literal["ACTIVE", "PAUSED", "WITHDRAWN"] | None = None
    memo: str | None = Field(default=None, max_length=5000)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    phone: str | None
    email: EmailStr | None
    birth_date: date | None
    guardian_name: str | None
    guardian_phone: str | None
    status: str
    memo: str | None


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    color: str = Field(default="#6474E8", pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("과목 이름을 입력해 주세요.")
        return value


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    name: str
    description: str | None
    color: str


class CourseCreate(BaseModel):
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("수업 이름을 입력해 주세요.")
        return value


class CourseUpdate(BaseModel):
    subject_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    status: Literal["ACTIVE", "PAUSED", "CLOSED"] | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    name: str
    description: str | None
    status: str
    subject_name: str
    teacher_name: str


class EnrollmentCreate(BaseModel):
    course_id: uuid.UUID
    student_id: uuid.UUID
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
        return self


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    start_date: date
    end_date: date | None
    status: str
    course_name: str
    student_name: str
