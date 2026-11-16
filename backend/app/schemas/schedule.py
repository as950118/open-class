import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScheduleCreate(BaseModel):
    course_id: uuid.UUID
    teacher_id: uuid.UUID | None = None
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    effective_start_date: date
    effective_end_date: date | None = None
    room: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.start_time >= self.end_time:
            raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다.")
        if self.effective_end_date and self.effective_end_date < self.effective_start_date:
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
        return self


class ScheduleUpdate(BaseModel):
    course_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    effective_start_date: date | None = None
    effective_end_date: date | None = None
    room: str | None = Field(default=None, max_length=80)
    status: Literal["ACTIVE", "CANCELLED"] | None = None


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    effective_start_date: date
    effective_end_date: date | None
    room: str | None
    status: str
    course_name: str
    teacher_name: str
    subject_name: str


class GenerateSessionsRequest(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_range(self):
        if self.end_date < self.start_date:
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
        if (self.end_date - self.start_date).days >= 90:
            raise ValueError("한 번에 최대 90일의 수업만 생성할 수 있습니다.")
        return self


class LessonSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    schedule_id: uuid.UUID | None
    scheduled_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    status: str
    room: str | None
    course_name: str
    teacher_name: str
    subject_name: str
    participant_count: int


class LessonSessionStudentRead(BaseModel):
    id: uuid.UUID
    lesson_session_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    attendance_status: str


class AttendanceUpdate(BaseModel):
    attendance_status: Literal["PRESENT", "ABSENT", "LATE", "EXCUSED"]


class SessionStatusUpdate(BaseModel):
    status: Literal["IN_PROGRESS", "COMPLETED", "CANCELLED"]
