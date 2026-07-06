"""Tests for the Student API endpoints."""
from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName, Strand
from app.models.learning_objective import LearningObjective
from app.models.student import Student
from app.models.student_record import StudentRecord, RatingLevel


def _seed_classroom(db_session, suffix: str) -> Classroom:
    """Helper to create a classroom."""
    classroom = Classroom(
        name=f"202{suffix}-202{int(suffix) + 1}",
        start_year=f"202{suffix}",
        end_year=f"202{int(suffix) + 1}",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom


def _seed_learning_objective(
    db_session, classroom_id: int, code: str
) -> LearningObjective:
    """Helper to create a learning objective."""
    goal_short_name = GoalShortName(
        name=f"Goal {code}",
        strand=Strand.CODING,
    )
    db_session.add(goal_short_name)
    db_session.commit()
    db_session.refresh(goal_short_name)

    lo = LearningObjective(
        code=code,
        description=f"Description for {code}",
        keywords=f"keyword-{code}",
        classroom_id=classroom_id,
        goal_short_name_id=goal_short_name.id,
    )
    db_session.add(lo)
    db_session.commit()
    db_session.refresh(lo)
    return lo


def test_list_students_with_records_returns_students_with_records(client, db_session):
    """Test that students with StudentRecords are returned."""
    classroom = _seed_classroom(db_session, "0")
    
    # Create students
    student_a = Student(name="Student A", classroom_id=classroom.id)
    student_b = Student(name="Student B", classroom_id=classroom.id)
    student_c = Student(name="Student C", classroom_id=classroom.id)  # No records
    
    db_session.add_all([student_a, student_b, student_c])
    db_session.commit()
    db_session.refresh(student_a)
    db_session.refresh(student_b)
    db_session.refresh(student_c)
    
    # Create learning objectives
    lo_1 = _seed_learning_objective(db_session, classroom.id, "LO-001")
    lo_2 = _seed_learning_objective(db_session, classroom.id, "LO-002")
    lo_3 = _seed_learning_objective(db_session, classroom.id, "LO-003")
    
    # Create student records
    # Student A: 3 records (different learning objectives)
    db_session.add(StudentRecord(
        student_id=student_a.id,
        learning_objective_id=lo_1.id,
        rating=RatingLevel.PROFICIENT
    ))
    db_session.add(StudentRecord(
        student_id=student_a.id,
        learning_objective_id=lo_2.id,
        rating=RatingLevel.BEGINNER
    ))
    db_session.add(StudentRecord(
        student_id=student_a.id,
        learning_objective_id=lo_3.id,
        rating=RatingLevel.EXEMPLARY
    ))
    
    # Student B: 1 record
    db_session.add(StudentRecord(
        student_id=student_b.id,
        learning_objective_id=lo_1.id,
        rating=RatingLevel.PROGRESSING
    ))
    
    db_session.commit()
    
    # Test endpoint with classroom filter
    response = client.get(f"/students/with-records?classroom_id={classroom.id}")
    assert response.status_code == 200
    
    result = response.json()
    assert len(result) == 2
    
    # Extract IDs and names
    returned_ids = {r["id"] for r in result}
    returned_names = {r["name"] for r in result}
    
    assert student_a.id in returned_ids
    assert student_b.id in returned_ids
    assert student_c.id not in returned_ids
    
    assert "Student A" in returned_names
    assert "Student B" in returned_names
    assert "Student C" not in returned_names


def test_list_students_with_records_no_duplicates(client, db_session):
    """Test that students with multiple records do not appear multiple times."""
    classroom = _seed_classroom(db_session, "1")
    
    student = Student(name="Student With Many Records", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    # Create 5 learning objectives and records
    learning_objectives = []
    for i in range(5):
        lo = _seed_learning_objective(db_session, classroom.id, f"LO-{i:03d}")
        learning_objectives.append(lo)
        db_session.add(StudentRecord(
            student_id=student.id,
            learning_objective_id=lo.id,
            rating=RatingLevel.PROFICIENT
        ))
    
    db_session.commit()
    
    # Test endpoint with classroom filter
    response = client.get(f"/students/with-records?classroom_id={classroom.id}")
    assert response.status_code == 200
    
    result = response.json()
    # Should return the student exactly once
    assert len(result) == 1
    assert result[0]["id"] == student.id
    assert result[0]["name"] == "Student With Many Records"


def test_list_students_with_records_excludes_students_without_records(
    client, db_session
):
    """Test that students without any StudentRecords are excluded."""
    classroom = _seed_classroom(db_session, "2")
    
    # Create students but no records
    students = [
        Student(name=f"Student {i}", classroom_id=classroom.id)
        for i in range(5)
    ]
    db_session.add_all(students)
    db_session.commit()
    
    # Test endpoint with classroom filter
    response = client.get(f"/students/with-records?classroom_id={classroom.id}")
    assert response.status_code == 200
    
    result = response.json()
    # Should return empty list
    assert len(result) == 0


def test_list_students_with_records_empty_result(client, db_session):
    """Test that endpoint handles empty results correctly."""
    # Create classroom and students but no records
    classroom = _seed_classroom(db_session, "3")
    student = Student(name="Lonely Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    
    # Test endpoint with classroom filter
    response = client.get(f"/students/with-records?classroom_id={classroom.id}")
    assert response.status_code == 200
    
    result = response.json()
    assert result == []


def test_list_students_with_records_ordering(client, db_session):
    """Test that students are returned in order by ID."""
    classroom = _seed_classroom(db_session, "4")
    
    students = [
        Student(name="Student Z", classroom_id=classroom.id),
        Student(name="Student A", classroom_id=classroom.id),
        Student(name="Student M", classroom_id=classroom.id),
    ]
    db_session.add_all(students)
    db_session.commit()
    for student in students:
        db_session.refresh(student)
    
    # Create learning objective
    lo = _seed_learning_objective(db_session, classroom.id, "LO-ORDER")
    
    # Add records for all students
    for student in students:
        db_session.add(StudentRecord(
            student_id=student.id,
            learning_objective_id=lo.id,
            rating=RatingLevel.PROFICIENT
        ))
    db_session.commit()
    
    # Test endpoint with classroom filter
    response = client.get(f"/students/with-records?classroom_id={classroom.id}")
    assert response.status_code == 200
    
    result = response.json()
    assert len(result) == 3
    
    # Verify ordering by ID
    returned_ids = [r["id"] for r in result]
    assert returned_ids == sorted(returned_ids)
    
    # Verify the IDs match our students in order
    expected_ids = [s.id for s in sorted(students, key=lambda s: s.id)]
    assert returned_ids == expected_ids


def test_list_students_with_records_classroom_isolation(client, db_session):
    """Test that endpoint filters correctly by classroom_id."""
    classroom_1 = _seed_classroom(db_session, "5")
    classroom_2 = _seed_classroom(db_session, "6")
    
    student_1 = Student(name="Student from Classroom 1", classroom_id=classroom_1.id)
    student_2 = Student(name="Student from Classroom 2", classroom_id=classroom_2.id)
    
    db_session.add_all([student_1, student_2])
    db_session.commit()
    db_session.refresh(student_1)
    db_session.refresh(student_2)
    
    # Create learning objectives
    lo_1 = _seed_learning_objective(db_session, classroom_1.id, "LO-C1")
    lo_2 = _seed_learning_objective(db_session, classroom_2.id, "LO-C2")
    
    # Add records
    db_session.add(StudentRecord(
        student_id=student_1.id,
        learning_objective_id=lo_1.id,
        rating=RatingLevel.PROFICIENT
    ))
    db_session.add(StudentRecord(
        student_id=student_2.id,
        learning_objective_id=lo_2.id,
        rating=RatingLevel.BEGINNER
    ))
    db_session.commit()
    
    # Test endpoint returns only students from classroom_1
    response_1 = client.get(f"/students/with-records?classroom_id={classroom_1.id}")
    assert response_1.status_code == 200
    result_1 = response_1.json()
    assert len(result_1) == 1
    assert result_1[0]["id"] == student_1.id
    
    # Test endpoint returns only students from classroom_2
    response_2 = client.get(f"/students/with-records?classroom_id={classroom_2.id}")
    assert response_2.status_code == 200
    result_2 = response_2.json()
    assert len(result_2) == 1
    assert result_2[0]["id"] == student_2.id


def test_list_students_with_records_schema_structure(client, db_session):
    """Test that the response schema is correct."""
    classroom = _seed_classroom(db_session, "7")
    
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    # Create learning objective and record
    lo = _seed_learning_objective(db_session, classroom.id, "LO-SCHEMA")
    db_session.add(StudentRecord(
        student_id=student.id,
        learning_objective_id=lo.id,
        rating=RatingLevel.PROFICIENT
    ))
    db_session.commit()
    
    # Test endpoint with classroom filter
    response = client.get(f"/students/with-records?classroom_id={classroom.id}")
    assert response.status_code == 200
    
    result = response.json()
    assert len(result) == 1
    
    student_data = result[0]
    # Verify schema structure
    assert "id" in student_data
    assert "name" in student_data
    assert "classroom_id" in student_data
    
    assert student_data["id"] == student.id
    assert student_data["name"] == "Test Student"
    assert student_data["classroom_id"] == classroom.id


def test_list_students_with_records_classroom_id_is_required(client, db_session):
    """Test that classroom_id parameter is mandatory."""
    # Create a classroom and students with records
    classroom = _seed_classroom(db_session, "8")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    lo = _seed_learning_objective(db_session, classroom.id, "LO-REQ")
    db_session.add(StudentRecord(
        student_id=student.id,
        learning_objective_id=lo.id,
        rating=RatingLevel.PROFICIENT
    ))
    db_session.commit()
    
    # Request without classroom_id should fail with 422 validation error
    response = client.get("/students/with-records")
    assert response.status_code == 422
