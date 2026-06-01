from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("Student name must not be blank")
        return normalized_value


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)