from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate

router = APIRouter(prefix="/classrooms", tags=["classrooms"])

@router.post("", response_model=ClassroomRead, status_code=status.HTTP_201_CREATED)
def create_classroom(payload: ClassroomCreate, db: Session = Depends(get_db)):
    # Check for existing classroom with same start_year and end_year
    existing = (
        db.query(Classroom)
        .filter(
            Classroom.start_year == payload.start_year,
            Classroom.end_year == payload.end_year,
        )
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A classroom for that period already exists",
        )

    classroom = Classroom(
        name=f"{payload.start_year}-{payload.end_year}",
        start_year=payload.start_year,
        end_year=payload.end_year,
    )

    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return classroom


@router.get("", response_model=list[ClassroomRead])
def list_classrooms(db: Session = Depends(get_db)):
    return db.query(Classroom).order_by(Classroom.id.asc()).all()

@router.put("/{classroom_id}", response_model=ClassroomRead)
def update_classroom(classroom_id: int, payload: ClassroomUpdate, db: Session = Depends(get_db)):
    classroom = db.get(Classroom, classroom_id)

    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    duplicate = (
        db.query(Classroom)
        .filter(
            Classroom.id != classroom_id,
            Classroom.start_year == payload.start_year,
            Classroom.end_year == payload.end_year,
        )
        .first()
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A classroom for that period already exists",
        )

    classroom.start_year = payload.start_year
    classroom.end_year = payload.end_year
    classroom.name = f"{payload.start_year}-{payload.end_year}"

    db.commit()
    db.refresh(classroom)

    return classroom


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(classroom_id: int, db: Session = Depends(get_db)):
    classroom = db.get(Classroom, classroom_id)

    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    db.delete(classroom)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)