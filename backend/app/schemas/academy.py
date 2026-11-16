import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AcademyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,39}$")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("학원 이름을 입력해 주세요.")
        return value


class AcademyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    status: str
