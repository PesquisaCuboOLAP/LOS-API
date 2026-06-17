from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.student_record import RatingLevel
from app.models.goal_short_name import Strand
from app.models.challenge import Semester

class ChallengeInfo(BaseModel):
    name: str
    semester: Optional[Semester] = None

    model_config = ConfigDict(from_attributes=True)


class LearningObjectiveExpandedRead(BaseModel):
    id: int
    code: str
    description: str
    keywords: str
    goal_short_name: str
    strand: Strand
    challenge: Optional[ChallengeInfo] = None

    model_config = ConfigDict(from_attributes=True)


class StudentRecordBase(BaseModel):
    rating: RatingLevel


class StudentRecordCreate(StudentRecordBase):
    student_id: int
    learning_objective_id: int


class StudentRecordUpdate(StudentRecordBase):
    pass


class StudentRecordUpdateByCode(BaseModel):
    """Update StudentRecord by learning objective code."""
    learning_objective_code: str = Field(..., min_length=1, description="Learning objective code")
    rating: RatingLevel

    model_config = ConfigDict(from_attributes=True)


class StudentRecordRead(StudentRecordBase):
    id: int
    student_id: int
    learning_objective_id: int
    learning_objective: LearningObjectiveExpandedRead

    model_config = ConfigDict(from_attributes=True)


class StudentRecordImportSummary(BaseModel):
    student_id: int
    imported_records: int
    updated_records: int
    missing_learning_objectives: list[str]
    skipped_empty_rows: int
