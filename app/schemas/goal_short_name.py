from pydantic import BaseModel, ConfigDict, Field

from app.models.goal_short_name import Strand


class GoalShortNameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    strand: Strand


class GoalShortNameCreate(GoalShortNameBase):
    pass


class GoalShortNameUpdate(GoalShortNameBase):
    pass


class GoalShortNameRead(GoalShortNameBase):
    id: int

    model_config = ConfigDict(from_attributes=True)