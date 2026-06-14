import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classroom import Classroom
from app.models.learning_objective import LearningObjective
from app.models.student import Student
from app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate
from app.schemas.learning_objective import LearningObjectiveRead
from app.schemas.student import StudentImportSummary, StudentRead

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


def _parse_student_import_csv(file: UploadFile) -> tuple[list[str], int]:
    try:
        content = file.file.read().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file format",
        ) from exc

    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty",
        )

    reader = csv.DictReader(StringIO(content))

    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file format",
        )
    
    reader.fieldnames = [
        field.strip() if field else field
        for field in reader.fieldnames
    ]

    normalized_headers = {header.strip() for header in reader.fieldnames if header}
    required_headers = {"name"}

    missing_headers = required_headers - normalized_headers
    if missing_headers:
        missing = ", ".join(sorted(missing_headers))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required CSV columns: {missing}",
        )

    student_names: list[str] = []
    skipped_empty_rows = 0

    for row in reader:
        if all(value is None or str(value).strip() == "" for value in row.values()):
            skipped_empty_rows += 1
            continue

        raw_name = row.get("name")
        name = raw_name.strip() if isinstance(raw_name, str) else ""

        student_names.append(name)

    if not student_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file does not contain any student rows",
        )

    return student_names, skipped_empty_rows

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


@router.get("/{classroom_id}/learning-objectives", response_model=list[LearningObjectiveRead])
def list_classroom_learning_objectives(
    classroom_id: int,
    db: Session = Depends(get_db),
):
    classroom = db.get(Classroom, classroom_id)

    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        )

    return (
        db.query(LearningObjective)
        .filter(LearningObjective.classroom_id == classroom_id)
        .order_by(LearningObjective.id.asc())
        .all()
    )

@router.get("/{classroom_id}/students", response_model=list[StudentRead])
def list_classroom_students(
    classroom_id: int,
    db: Session = Depends(get_db),
):
    classroom = db.get(Classroom, classroom_id)

    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )

    return (
        db.query(Student)
        .filter(Student.classroom_id == classroom_id)
        .order_by(Student.name.asc())
        .all()
    )


@router.post(
    "/{classroom_id}/students/import",
    response_model=StudentImportSummary,
    status_code=status.HTTP_201_CREATED,
)
def import_classroom_students(
    classroom_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    classroom = db.get(Classroom, classroom_id)

    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        )

    student_names, skipped_empty_rows = _parse_student_import_csv(file)

    students = [
        Student(name=name, classroom_id=classroom_id)
        for name in student_names
    ]

    db.bulk_save_objects(students)
    db.commit()

    return StudentImportSummary(
        classroom_id=classroom_id,
        imported_students=len(students),
        skipped_empty_rows=skipped_empty_rows,
    )

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
    
    has_students = (
        db.query(Student)
        .filter(Student.classroom_id == classroom_id)
        .first()
    )

    if has_students:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a classroom with assigned students",
        )

    db.delete(classroom)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)