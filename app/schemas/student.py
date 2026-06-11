from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)