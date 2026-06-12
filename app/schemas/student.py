from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    classroom_id: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class StudentRead(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StudentImportSummary(BaseModel):
    classroom_id: int
    imported_students: int
    skipped_empty_rows: int