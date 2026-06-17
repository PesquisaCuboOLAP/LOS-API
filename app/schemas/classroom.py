from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.student_record import RatingLevel
from app.models.goal_short_name import Strand
from app.models.challenge import Semester

class ClassroomBase(BaseModel):
    start_year: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
    end_year: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class ClassroomCreate(ClassroomBase):
    pass    

class ClassroomUpdate(ClassroomBase):
    pass

class ClassroomRead(ClassroomBase):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ChallengeMetadata(BaseModel):
    """Metadata for a challenge."""
    id: int
    name: str
    semester: Optional[Semester] = None

    model_config = ConfigDict(from_attributes=True)


class GoalShortNameMetadata(BaseModel):
    """Metadata for a goal short name."""
    id: int
    name: str
    strand: Strand

    model_config = ConfigDict(from_attributes=True)


class ClassroomMetadata(BaseModel):
    """Comprehensive metadata for a classroom."""
    classroom_id: int
    classroom_name: str
    rating_levels: list[str]  # All possible RatingLevel values
    strands: list[str]  # All possible Strand values
    challenges: list[ChallengeMetadata]
    goal_short_names: list[GoalShortNameMetadata]

    model_config = ConfigDict(from_attributes=True)