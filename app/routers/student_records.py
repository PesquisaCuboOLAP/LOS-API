import csv
from dataclasses import dataclass
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.challenge import Challenge
from app.models.learning_objective import LearningObjective
from app.models.student import Student
from app.models.student_record import StudentRecord, RatingLevel
from app.schemas.student_record import StudentRecordRead, StudentRecordImportSummary, StudentRecordUpdateByCode

router = APIRouter(prefix="/students", tags=["student-records"])

CODE_HEADER = "código"
LEVEL_HEADER = "level"

REQUIRED_HEADERS = {
    CODE_HEADER,
    LEVEL_HEADER,
}

def detect_delimiter(content: str) -> str:
    if not content.strip():
        return ","

    try:
        dialect = csv.Sniffer().sniff(
            content[:2048],
            delimiters=",;|\t"
        )
        return dialect.delimiter
    except csv.Error:
        return ","

def _read_csv_upload(file: UploadFile) -> str:
    try:
        content = file.file.read().decode("utf-8-sig")
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

    return content

def validate_csv_headers(reader: csv.DictReader) -> None:
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file format",
        )

    normalized_headers = {
        field.strip().lower()
        for field in reader.fieldnames
    }

    missing_headers = REQUIRED_HEADERS - normalized_headers

    if missing_headers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required CSV columns: {', '.join(missing_headers)}",
        )
    
def get_csv_rows(reader: csv.DictReader) -> list[dict]:
    rows = list(reader)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file does not contain any data rows",
        )

    return rows

def extract_codes(rows: list[dict]) -> set[str]:
    return {
        row[CODE_HEADER].strip()
        for row in rows
        if row.get(CODE_HEADER)
        and row[CODE_HEADER].strip()
    }

def load_learning_objectives(
    db: Session,
    codes: set[str],
) -> dict[str, LearningObjective]:

    learning_objectives = db.execute(
        select(LearningObjective)
        .where(LearningObjective.code.in_(codes))
    ).scalars().all()

    lo_by_code = {
        lo.code: lo
        for lo in learning_objectives
    }

    missing_codes = sorted(
        codes - set(lo_by_code.keys())
    )

    if missing_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The following Learning Objectives "
                f"do not exist: {', '.join(missing_codes)}"
            ),
        )

    return lo_by_code

def parse_rating(code: str, raw_rating: str) -> RatingLevel:
    rating_map = {
        r.value.upper(): r
        for r in RatingLevel
    }

    rating = rating_map.get(raw_rating)

    if not rating and raw_rating == "NÃO INICIADO":
        rating = RatingLevel.NOT_STARTED

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rating value '{raw_rating}' for code {code}",
        )

    return rating

def import_records(
    db: Session,
    student_id: int,
    rows: list[dict],
    lo_by_code: dict[str, LearningObjective],
) -> tuple[int, int, int]:

    existing_records = db.execute(
        select(StudentRecord)
        .where(StudentRecord.student_id == student_id)
    ).scalars().all()

    records_by_lo_id = {
        record.learning_objective_id: record
        for record in existing_records
    }

    imported = 0
    updated = 0
    skipped = 0

    for row in rows:
        code = row[CODE_HEADER].strip()
        raw_rating = row[LEVEL_HEADER].strip().upper()

        if not code or not raw_rating:
            skipped += 1
            continue

        lo = lo_by_code[code]
        rating = parse_rating(code, raw_rating)

        existing = records_by_lo_id.get(lo.id)

        if existing:
            if existing.rating != rating:
                existing.rating = rating
                updated += 1
        else:
            db.add(
                StudentRecord(
                    student_id=student_id,
                    learning_objective_id=lo.id,
                    rating=rating,
                )
            )
            imported += 1

    return imported, updated, skipped

@router.post(
    "/{student_id}/records/import",
    response_model=StudentRecordImportSummary,
    status_code=status.HTTP_201_CREATED,
)
def import_student_records(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    content = _read_csv_upload(file)
    delimiter = detect_delimiter(content)
    reader = csv.DictReader(StringIO(content), delimiter=delimiter)
    reader.fieldnames = [
        field.strip().lower()
        for field in reader.fieldnames
    ]

    validate_csv_headers(reader)
    rows = get_csv_rows(reader)

    codes = extract_codes(rows)
    lo_by_code = load_learning_objectives(db, codes)

    imported_count, updated_count, skipped_empty_rows = import_records(
        db,
        student_id,
        rows,
        lo_by_code,
    )

    db.commit()

    return StudentRecordImportSummary(
        student_id=student_id,
        imported_records=imported_count,
        updated_records=updated_count,
        missing_learning_objectives=[],
        skipped_empty_rows=skipped_empty_rows,
    )


@router.get(
    "/{student_id}/records", 
    response_model=list[StudentRecordRead]
)
def get_student_records(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Use eager loading to avoid N+1 queries
    records = db.execute(
        select(StudentRecord)
        .where(StudentRecord.student_id == student_id)
        .options(
            joinedload(StudentRecord.learning_objective)
            .joinedload(LearningObjective.goal_short_name)
        )
    ).scalars().all()

    # Fetch challenges to map LOs to Challenge/Semester
    all_challenges = db.execute(select(Challenge)).scalars().all()
    lo_to_challenge = {}
    for chal in all_challenges:
        for lo_id in chal.learning_objective_ids:
            if lo_id not in lo_to_challenge:
                lo_to_challenge[lo_id] = chal

    # Map database models to the expanded schema structure
    results = []
    for rec in records:
        lo = rec.learning_objective
        gsn = lo.goal_short_name
        chal = lo_to_challenge.get(lo.id)
        
        result = {
            "id": rec.id,
            "student_id": rec.student_id,
            "learning_objective_id": rec.learning_objective_id,
            "rating": rec.rating,
            "learning_objective": {
                "id": lo.id,
                "code": lo.code,
                "description": lo.description,
                "keywords": lo.keywords,
                "goal_short_name": gsn.name,
                "strand": gsn.strand,
                "challenge": {
                    "name": chal.name,
                    "semester": chal.semester
                } if chal else None
            }
        }
        results.append(result)

    return results


@router.put(
    "/{student_id}/records", 
    response_model=StudentRecordRead
)
def update_student_record(
    student_id: int,
    payload: StudentRecordUpdateByCode,
    db: Session = Depends(get_db),
) -> StudentRecordRead:
    """
    Updates a student's record by learning objective code.
    
    Args:
        student_id: The ID of the student.
        payload: Contains learning_objective_code and rating.
        db: Database session.
    
    Returns:
        Updated StudentRecordRead object.
    """
    # Verify student exists
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    
    # Find learning objective by code
    learning_objective = db.execute(
        select(LearningObjective).where(
            (LearningObjective.code == payload.learning_objective_code) &
            (LearningObjective.classroom_id == student.classroom_id)
        )
    ).scalars().first()
    
    if not learning_objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning objective with code '{payload.learning_objective_code}' not found",
        )
    
    # Validate rating is a valid RatingLevel
    rating_level = payload.rating
    
    # Find or create the StudentRecord
    record = db.execute(
        select(StudentRecord).where(
            (StudentRecord.student_id == student_id) &
            (StudentRecord.learning_objective_id == learning_objective.id)
        )
    ).scalars().first()
    
    if not record:
        # Create new record
        record = StudentRecord(
            student_id=student_id,
            learning_objective_id=learning_objective.id,
            rating=rating_level
        )
        db.add(record)
    else:
        # Update existing record
        record.rating = rating_level
    
    db.commit()
    db.refresh(record)
    
    # Eagerly load the relationship for response
    db.refresh(record, ["learning_objective"])
    db.refresh(record.learning_objective, ["goal_short_name"])
    
    # Fetch challenges to map LOs to Challenge/Semester
    all_challenges = db.execute(select(Challenge)).scalars().all()
    lo_to_challenge = {}
    for chal in all_challenges:
        for lo_id in chal.learning_objective_ids:
            if lo_id not in lo_to_challenge:
                lo_to_challenge[lo_id] = chal
    
    # Build the response
    lo = record.learning_objective
    gsn = lo.goal_short_name
    chal = lo_to_challenge.get(lo.id)
    
    return {
        "id": record.id,
        "student_id": record.student_id,
        "learning_objective_id": record.learning_objective_id,
        "rating": record.rating,
        "learning_objective": {
            "id": lo.id,
            "code": lo.code,
            "description": lo.description,
            "keywords": lo.keywords,
            "goal_short_name": gsn.name,
            "strand": gsn.strand,
            "challenge": {
                "name": chal.name,
                "semester": chal.semester
            } if chal else None
        }
    }


@router.delete("/{student_id}/records", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_records(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.execute(
        StudentRecord.__table__.delete().where(StudentRecord.student_id == student_id)
    )
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
