from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName
from app.models.learning_objective import LearningObjective
from app.schemas.learning_objective import (
    LearningObjectiveCreate,
    LearningObjectiveRead,
    LearningObjectiveUpdate,
)


router = APIRouter(prefix="/learning-objectives", tags=["learning-objectives"])


def _get_classroom_or_404(classroom_id: int, db: Session) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        )
    return classroom


def _get_goal_short_name_or_404(goal_short_name_id: int, db: Session) -> GoalShortName:
    goal_short_name = db.get(GoalShortName, goal_short_name_id)
    if goal_short_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal short name not found",
        )
    return goal_short_name


@router.post("", response_model=LearningObjectiveRead, status_code=status.HTTP_201_CREATED)
def create_learning_objective(payload: LearningObjectiveCreate, db: Session = Depends(get_db)):
    _get_classroom_or_404(payload.classroom_id, db)
    _get_goal_short_name_or_404(payload.goal_short_name_id, db)

    learning_objective = LearningObjective(
        code=payload.code.strip(),
        description=payload.description.strip(),
        keywords=payload.keywords.strip(),
        classroom_id=payload.classroom_id,
        goal_short_name_id=payload.goal_short_name_id,
    )
    db.add(learning_objective)
    db.commit()
    db.refresh(learning_objective)
    return learning_objective


@router.get("", response_model=list[LearningObjectiveRead])
def list_learning_objectives(db: Session = Depends(get_db)):
    return db.query(LearningObjective).order_by(LearningObjective.id.asc()).all()


@router.get("/{learning_objective_id}", response_model=LearningObjectiveRead)
def get_learning_objective(learning_objective_id: int, db: Session = Depends(get_db)):
    learning_objective = db.get(LearningObjective, learning_objective_id)
    if learning_objective is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning objective not found",
        )
    return learning_objective


@router.put("/{learning_objective_id}", response_model=LearningObjectiveRead)
def update_learning_objective(
    learning_objective_id: int,
    payload: LearningObjectiveUpdate,
    db: Session = Depends(get_db),
):
    learning_objective = db.get(LearningObjective, learning_objective_id)
    if learning_objective is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning objective not found",
        )

    _get_classroom_or_404(payload.classroom_id, db)
    _get_goal_short_name_or_404(payload.goal_short_name_id, db)

    learning_objective.code = payload.code.strip()
    learning_objective.description = payload.description.strip()
    learning_objective.keywords = payload.keywords.strip()
    learning_objective.classroom_id = payload.classroom_id
    learning_objective.goal_short_name_id = payload.goal_short_name_id

    db.commit()
    db.refresh(learning_objective)
    return learning_objective


@router.delete("/{learning_objective_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learning_objective(learning_objective_id: int, db: Session = Depends(get_db)):
    learning_objective = db.get(LearningObjective, learning_objective_id)
    if learning_objective is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning objective not found",
        )

    db.delete(learning_objective)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)