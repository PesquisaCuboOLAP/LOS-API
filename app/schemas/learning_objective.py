from pydantic import BaseModel, ConfigDict, Field

from app.models.challenge import Semester


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


class LearningObjectiveImportSummary(BaseModel):
    classroom_id: int
    semester: Semester
    total_rows: int
    imported_goal_short_names: int
    reused_goal_short_names: int
    imported_learning_objectives: int
    skipped_duplicate_learning_objectives: int
    skipped_duplicate_rows_in_file: int
    created_challenges: int
    updated_challenges: int
    skipped_empty_rows: int