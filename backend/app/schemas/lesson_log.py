import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LessonLogCreate(BaseModel):
    lesson_session_id: uuid.UUID
    student_id: uuid.UUID
    subject: str | None = Field(default=None, max_length=160)
    lesson_content: str = Field(min_length=1, max_length=12000)
    progress_content: str | None = Field(default=None, max_length=6000)
    understanding_level: int | None = Field(default=None, ge=1, le=5)
    homework: str | None = Field(default=None, max_length=6000)
    feedback: str | None = Field(default=None, max_length=6000)
    next_plan: str | None = Field(default=None, max_length=6000)


class LessonLogUpdate(BaseModel):
    subject: str | None = Field(default=None, max_length=160)
    lesson_content: str | None = Field(default=None, min_length=1, max_length=12000)
    progress_content: str | None = Field(default=None, max_length=6000)
    understanding_level: int | None = Field(default=None, ge=1, le=5)
    homework: str | None = Field(default=None, max_length=6000)
    feedback: str | None = Field(default=None, max_length=6000)
    next_plan: str | None = Field(default=None, max_length=6000)


class LessonLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    academy_id: uuid.UUID
    lesson_session_id: uuid.UUID
    teacher_id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    course_name: str
    teacher_name: str
    student_name: str
    subject_name: str
    subject: str | None
    lesson_content: str
    progress_content: str | None
    understanding_level: int | None
    homework: str | None
    feedback: str | None
    next_plan: str | None
    scheduled_at: datetime
    created_at: datetime
    updated_at: datetime
