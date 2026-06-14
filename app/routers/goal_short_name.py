from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.goal_short_name import GoalShortName
from app.models.learning_objective import LearningObjective
from app.schemas.goal_short_name import (
    GoalShortNameCreate,
    GoalShortNameRead,
    GoalShortNameUpdate,
)


router = APIRouter(prefix="/goal-short-names", tags=["goal-short-names"])


@router.post("", response_model=GoalShortNameRead, status_code=status.HTTP_201_CREATED)
def create_goal_short_name(payload: GoalShortNameCreate, db: Session = Depends(get_db)):
    normalized_name = payload.name.strip()

    existing = (
        db.query(GoalShortName)
        .filter(GoalShortName.name == normalized_name)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Goal short name already exists",
        )

    goal_short_name = GoalShortName(
        name=normalized_name,
        strand=payload.strand,
    )
    db.add(goal_short_name)
    db.commit()
    db.refresh(goal_short_name)
    return goal_short_name


@router.get("", response_model=list[GoalShortNameRead])
def list_goal_short_names(db: Session = Depends(get_db)):
    return db.query(GoalShortName).order_by(GoalShortName.id.asc()).all()


@router.get("/{goal_short_name_id}", response_model=GoalShortNameRead)
def get_goal_short_name(goal_short_name_id: int, db: Session = Depends(get_db)):
    goal_short_name = db.get(GoalShortName, goal_short_name_id)
    if goal_short_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal short name not found",
        )
    return goal_short_name


@router.put("/{goal_short_name_id}", response_model=GoalShortNameRead)
def update_goal_short_name(
    goal_short_name_id: int,
    payload: GoalShortNameUpdate,
    db: Session = Depends(get_db),
):
    goal_short_name = db.get(GoalShortName, goal_short_name_id)
    if goal_short_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal short name not found",
        )

    normalized_name = payload.name.strip()
    duplicate = (
        db.query(GoalShortName)
        .filter(
            GoalShortName.id != goal_short_name_id,
            GoalShortName.name == normalized_name,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Goal short name already exists",
        )

    goal_short_name.name = normalized_name
    goal_short_name.strand = payload.strand
    db.commit()
    db.refresh(goal_short_name)
    return goal_short_name


@router.delete("/{goal_short_name_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal_short_name(goal_short_name_id: int, db: Session = Depends(get_db)):
    goal_short_name = db.get(GoalShortName, goal_short_name_id)
    if goal_short_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal short name not found",
        )

    has_learning_objectives = (
        db.query(LearningObjective)
        .filter(LearningObjective.goal_short_name_id == goal_short_name_id)
        .first()
    )
    if has_learning_objectives is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a goal short name with linked learning objectives",
        )

    db.delete(goal_short_name)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)