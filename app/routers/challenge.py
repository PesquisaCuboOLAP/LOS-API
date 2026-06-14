from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.challenge import Challenge
from app.models.learning_objective import LearningObjective
from app.schemas.challenge import ChallengeCreate, ChallengeRead, ChallengeUpdate


router = APIRouter(prefix="/challenges", tags=["challenges"])


def _validate_learning_objective_ids(ids: list[int], db: Session) -> None:
    unique_ids = set(ids)
    if not unique_ids:
        return

    found_ids = {
        learning_objective_id
        for (learning_objective_id,) in (
            db.query(LearningObjective.id)
            .filter(LearningObjective.id.in_(unique_ids))
            .all()
        )
    }
    missing_ids = sorted(unique_ids - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"missing_learning_objective_ids": missing_ids},
        )


@router.post("", response_model=ChallengeRead, status_code=status.HTTP_201_CREATED)
def create_challenge(payload: ChallengeCreate, db: Session = Depends(get_db)):
    _validate_learning_objective_ids(payload.learning_objective_ids, db)

    challenge = Challenge(
        name=payload.name.strip(),
        semester=payload.semester,
        learning_objective_ids=payload.learning_objective_ids,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("", response_model=list[ChallengeRead])
def list_challenges(db: Session = Depends(get_db)):
    return db.query(Challenge).order_by(Challenge.id.asc()).all()


@router.get("/{challenge_id}", response_model=ChallengeRead)
def get_challenge(challenge_id: int, db: Session = Depends(get_db)):
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    return challenge


@router.put("/{challenge_id}", response_model=ChallengeRead)
def update_challenge(
    challenge_id: int,
    payload: ChallengeUpdate,
    db: Session = Depends(get_db),
):
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )

    _validate_learning_objective_ids(payload.learning_objective_ids, db)

    challenge.name = payload.name.strip()
    challenge.semester = payload.semester
    challenge.learning_objective_ids = payload.learning_objective_ids

    db.commit()
    db.refresh(challenge)
    return challenge


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(challenge_id: int, db: Session = Depends(get_db)):
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )

    db.delete(challenge)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)