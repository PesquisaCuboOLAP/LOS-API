from pydantic import BaseModel, ConfigDict, Field


class LearningObjectiveBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    keywords: str = Field(..., min_length=1)
    goal_short_name_id: int
    classroom_id: int


class LearningObjectiveCreate(LearningObjectiveBase):
    pass


class LearningObjectiveUpdate(LearningObjectiveBase):
    pass


class LearningObjectiveRead(LearningObjectiveBase):
    id: int

    model_config = ConfigDict(from_attributes=True)