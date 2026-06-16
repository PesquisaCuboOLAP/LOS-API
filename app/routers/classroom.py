import csv
from dataclasses import dataclass
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.challenge import Challenge, Semester
from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName, Strand
from app.models.learning_objective import LearningObjective
from app.models.student import Student
from app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate
from app.schemas.learning_objective import LearningObjectiveImportSummary, LearningObjectiveRead
from app.schemas.student import StudentImportSummary, StudentRead

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


LEARNING_OBJECTIVE_IMPORT_REQUIRED_HEADERS = {
    "Code",
    "Learning Strand",
    "Goal Short Name",
    "Learning Objective",
    "Learning Objective Keywords",
    "Challenge",
}

STRAND_BY_LABEL = {
    "MARKETING": Strand.MARKETING,
    "CODING": Strand.CODING,
    "DESIGN": Strand.DESIGN,
    "PROCESS": Strand.PROCESS,
    "PROFESSIONAL SKILLS": Strand.PROFESSIONAL_SKILLS,
}


@dataclass(frozen=True)
class LearningObjectiveImportRow:
    row_number: int
    code: str
    strand: Strand
    goal_short_name: str
    description: str
    keywords: str
    challenge_name: str


def _read_csv_upload(file: UploadFile) -> str:
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

    return content


def _normalize_csv_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_strand(value: str, row_number: int) -> Strand:
    normalized = " ".join(value.upper().split())
    strand = STRAND_BY_LABEL.get(normalized)
    if strand is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid learning strand at row {row_number}: {value}",
        )
    return strand


def _parse_learning_objective_import_csv(
    file: UploadFile,
) -> tuple[list[LearningObjectiveImportRow], int]:
    content = _read_csv_upload(file)
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
    missing_headers = LEARNING_OBJECTIVE_IMPORT_REQUIRED_HEADERS - normalized_headers
    if missing_headers:
        missing = ", ".join(sorted(missing_headers))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required CSV columns: {missing}",
        )

    rows: list[LearningObjectiveImportRow] = []
    skipped_empty_rows = 0

    for row_number, raw_row in enumerate(reader, start=2):
        normalized_row = {
            key.strip() if isinstance(key, str) else key: _normalize_csv_value(value)
            for key, value in raw_row.items()
        }

        if all(value == "" for value in normalized_row.values()):
            skipped_empty_rows += 1
            continue

        missing_values = [
            header
            for header in sorted(LEARNING_OBJECTIVE_IMPORT_REQUIRED_HEADERS)
            if normalized_row.get(header, "") == ""
        ]
        if missing_values:
            missing = ", ".join(missing_values)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required CSV values at row {row_number}: {missing}",
            )

        rows.append(
            LearningObjectiveImportRow(
                row_number=row_number,
                code=normalized_row["Code"],
                strand=_normalize_strand(normalized_row["Learning Strand"], row_number),
                goal_short_name=normalized_row["Goal Short Name"],
                description=normalized_row["Learning Objective"],
                keywords=normalized_row["Learning Objective Keywords"],
                challenge_name=normalized_row["Challenge"],
            )
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file does not contain any learning objective rows",
        )

    return rows, skipped_empty_rows


def _parse_student_import_csv(file: UploadFile) -> tuple[list[str], int]:
    content = _read_csv_upload(file)
    reader = csv.DictReader(
        StringIO(content),
        delimiter=";"
    )

    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file format",
        )
    
    reader.fieldnames = [
        field.strip().lower() if field else field
        for field in reader.fieldnames
    ]

    normalized_headers = {header.strip().lower() for header in reader.fieldnames if header}
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


@router.post(
    "/{classroom_id}/learning-objectives/import/{semester}",
    response_model=LearningObjectiveImportSummary,
    status_code=status.HTTP_201_CREATED,
)
def import_classroom_learning_objectives(
    classroom_id: int,
    semester: Semester,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    classroom = db.get(Classroom, classroom_id)

    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        )

    parsed_rows, skipped_empty_rows = _parse_learning_objective_import_csv(file)
    total_rows = len(parsed_rows)

    unique_rows: list[LearningObjectiveImportRow] = []
    seen_codes: set[str] = set()
    skipped_duplicate_rows_in_file = 0

    for row in parsed_rows:
        if row.code in seen_codes:
            skipped_duplicate_rows_in_file += 1
            continue
        seen_codes.add(row.code)
        unique_rows.append(row)

    goal_short_name_to_strand: dict[str, Strand] = {}
    for row in unique_rows:
        existing_strand = goal_short_name_to_strand.get(row.goal_short_name)
        if existing_strand is not None and existing_strand != row.strand:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Goal short name has conflicting strands in import file: "
                    f"{row.goal_short_name}"
                ),
            )
        goal_short_name_to_strand[row.goal_short_name] = row.strand

    goal_short_name_names = set(goal_short_name_to_strand)
    existing_goal_short_names = (
        db.query(GoalShortName)
        .filter(GoalShortName.name.in_(goal_short_name_names))
        .all()
    )
    goal_short_names_by_name = {
        goal_short_name.name: goal_short_name
        for goal_short_name in existing_goal_short_names
    }

    reused_goal_short_name_names: set[str] = set()
    created_goal_short_names: list[GoalShortName] = []

    for goal_short_name_name, strand in goal_short_name_to_strand.items():
        existing_goal_short_name = goal_short_names_by_name.get(goal_short_name_name)
        if existing_goal_short_name is None:
            created_goal_short_names.append(
                GoalShortName(name=goal_short_name_name, strand=strand)
            )
            continue

        if existing_goal_short_name.strand != strand:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Goal short name already exists with a different strand: "
                    f"{goal_short_name_name}"
                ),
            )

        reused_goal_short_name_names.add(goal_short_name_name)

    if created_goal_short_names:
        db.add_all(created_goal_short_names)
        db.flush()
        for goal_short_name in created_goal_short_names:
            goal_short_names_by_name[goal_short_name.name] = goal_short_name

    existing_learning_objectives = (
        db.query(LearningObjective)
        .filter(
            LearningObjective.classroom_id == classroom_id,
            LearningObjective.code.in_(seen_codes),
        )
        .all()
    )
    existing_learning_objectives_by_code = {
        learning_objective.code: learning_objective
        for learning_objective in existing_learning_objectives
    }

    imported_learning_objectives = 0
    skipped_duplicate_learning_objectives = 0
    new_learning_objectives: list[tuple[str, LearningObjective]] = []
    challenge_learning_objective_ids: dict[str, set[int]] = {}

    for row in unique_rows:
        challenge_learning_objective_ids.setdefault(row.challenge_name, set())
        existing_learning_objective = existing_learning_objectives_by_code.get(row.code)
        if existing_learning_objective is not None:
            skipped_duplicate_learning_objectives += 1
            challenge_learning_objective_ids[row.challenge_name].add(existing_learning_objective.id)
            continue

        learning_objective = LearningObjective(
            code=row.code,
            description=row.description,
            keywords=row.keywords,
            classroom_id=classroom_id,
            goal_short_name_id=goal_short_names_by_name[row.goal_short_name].id,
        )
        db.add(learning_objective)
        new_learning_objectives.append((row.challenge_name, learning_objective))
        imported_learning_objectives += 1

    if new_learning_objectives:
        db.flush()
        for challenge_name, learning_objective in new_learning_objectives:
            challenge_learning_objective_ids[challenge_name].add(learning_objective.id)

    challenge_names = set(challenge_learning_objective_ids)
    existing_challenges = (
        db.query(Challenge)
        .filter(Challenge.name.in_(challenge_names))
        .all()
    )
    challenges_by_name = {
        challenge.name: challenge
        for challenge in existing_challenges
    }

    created_challenges = 0
    updated_challenges = 0

    for challenge_name, learning_objective_ids in challenge_learning_objective_ids.items():
        ordered_import_ids = sorted(learning_objective_ids)
        challenge = challenges_by_name.get(challenge_name)

        if challenge is None:
            challenge = Challenge(
                name=challenge_name,
                semester=semester,
                learning_objective_ids=ordered_import_ids,
            )
            db.add(challenge)
            challenges_by_name[challenge_name] = challenge
            created_challenges += 1
            continue

        semester_was_updated = False
        if challenge.semester is None:
            challenge.semester = semester
            semester_was_updated = True
        elif challenge.semester != semester:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Challenge already exists with a different semester: "
                    f"{challenge_name}"
                ),
            )

        merged_learning_objective_ids = list(challenge.learning_objective_ids)
        for learning_objective_id in ordered_import_ids:
            if learning_objective_id not in merged_learning_objective_ids:
                merged_learning_objective_ids.append(learning_objective_id)

        if semester_was_updated or merged_learning_objective_ids != challenge.learning_objective_ids:
            challenge.learning_objective_ids = merged_learning_objective_ids
            updated_challenges += 1

    db.commit()

    return LearningObjectiveImportSummary(
        classroom_id=classroom_id,
        semester=semester,
        total_rows=total_rows,
        imported_goal_short_names=len(created_goal_short_names),
        reused_goal_short_names=len(reused_goal_short_name_names),
        imported_learning_objectives=imported_learning_objectives,
        skipped_duplicate_learning_objectives=skipped_duplicate_learning_objectives,
        skipped_duplicate_rows_in_file=skipped_duplicate_rows_in_file,
        created_challenges=created_challenges,
        updated_challenges=updated_challenges,
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