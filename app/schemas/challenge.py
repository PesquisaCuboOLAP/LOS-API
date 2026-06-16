from pydantic import BaseModel, ConfigDict, Field

from app.models.challenge import Semester


class ChallengeBase(BaseModel):
    name: str = Field(..., min_length=1)
    semester: Semester = Semester.FIRST
    learning_objective_ids: list[int] = Field(default_factory=list)


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeUpdate(ChallengeBase):
    pass


class ChallengeRead(BaseModel):
    id: int
    name: str
    semester: Semester | None = None
    learning_objective_ids: list[int]

    model_config = ConfigDict(from_attributes=True)