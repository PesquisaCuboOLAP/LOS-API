"""Tests for StudentRecord update and Classroom metadata endpoints."""
from app.models.classroom import Classroom
from app.models.challenge import Challenge, Semester
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


def _seed_challenge(db_session, name: str, semester: Semester, lo_ids: list[int]) -> Challenge:
    """Helper to create a challenge."""
    challenge = Challenge(
        name=name,
        semester=semester,
        learning_objective_ids=lo_ids,
    )
    db_session.add(challenge)
    db_session.commit()
    db_session.refresh(challenge)
    return challenge


# ============================================================================
# Tests for PUT endpoint: Update StudentRecord by learning objective code
# ============================================================================

def test_update_student_record_creates_new_record(client, db_session):
    """Test creating a new StudentRecord via PUT endpoint."""
    classroom = _seed_classroom(db_session, "0")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    lo = _seed_learning_objective(db_session, classroom.id, "LO-CREATE-001")
    
    # Update record (create new)
    response = client.put(
        f"/students/{student.id}/records",
        json={
            "learning_objective_code": "LO-CREATE-001",
            "rating": "PROFICIENT"
        }
    )
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["student_id"] == student.id
    assert result["learning_objective_id"] == lo.id
    assert result["rating"] == "PROFICIENT"
    assert result["learning_objective"]["code"] == "LO-CREATE-001"


def test_update_student_record_updates_existing_record(client, db_session):
    """Test updating an existing StudentRecord."""
    classroom = _seed_classroom(db_session, "1")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    lo = _seed_learning_objective(db_session, classroom.id, "LO-UPDATE-001")
    
    # Create initial record
    db_session.add(StudentRecord(
        student_id=student.id,
        learning_objective_id=lo.id,
        rating=RatingLevel.BEGINNER
    ))
    db_session.commit()
    
    # Update the record
    response = client.put(
        f"/students/{student.id}/records",
        json={
            "learning_objective_code": "LO-UPDATE-001",
            "rating": "EXEMPLARY"
        }
    )
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["rating"] == "EXEMPLARY"
    
    # Verify in database that only one record exists
    records = db_session.query(StudentRecord).filter(
        StudentRecord.student_id == student.id
    ).all()
    assert len(records) == 1
    assert records[0].rating == RatingLevel.EXEMPLARY


def test_update_student_record_invalid_learning_objective(client, db_session):
    """Test updating with non-existent learning objective."""
    classroom = _seed_classroom(db_session, "2")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    response = client.put(
        f"/students/{student.id}/records",
        json={
            "learning_objective_code": "NONEXISTENT",
            "rating": "PROFICIENT"
        }
    )
    
    assert response.status_code == 404
    assert "Learning objective" in response.json()["detail"]


def test_update_student_record_invalid_rating(client, db_session):
    """Test updating with invalid rating value."""
    classroom = _seed_classroom(db_session, "3")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    _seed_learning_objective(db_session, classroom.id, "LO-RATE-001")
    
    response = client.put(
        f"/students/{student.id}/records",
        json={
            "learning_objective_code": "LO-RATE-001",
            "rating": "INVALID_RATING"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_update_student_record_student_not_found(client, db_session):
    """Test updating record for non-existent student."""
    response = client.put(
        "/students/99999/records",
        json={
            "learning_objective_code": "LO-TEST",
            "rating": "PROFICIENT"
        }
    )
    
    assert response.status_code == 404
    assert "Student not found" in response.json()["detail"]


def test_update_student_record_all_rating_levels(client, db_session):
    """Test that all RatingLevel values are accepted."""
    classroom = _seed_classroom(db_session, "4")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    # Create multiple learning objectives
    los = []
    for i, level in enumerate(RatingLevel):
        lo = _seed_learning_objective(db_session, classroom.id, f"LO-RATING-{i:02d}")
        los.append((lo, level))
    
    # Test each rating level
    for lo, level in los:
        response = client.put(
            f"/students/{student.id}/records",
            json={
                "learning_objective_code": lo.code,
                "rating": level.value
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["rating"] == level.value


def test_update_student_record_response_schema(client, db_session):
    """Test that response includes all required fields."""
    classroom = _seed_classroom(db_session, "5")
    student = Student(name="Test Student", classroom_id=classroom.id)
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    
    lo = _seed_learning_objective(db_session, classroom.id, "LO-SCHEMA-001")
    
    response = client.put(
        f"/students/{student.id}/records",
        json={
            "learning_objective_code": "LO-SCHEMA-001",
            "rating": "PROFICIENT"
        }
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # Check all required fields
    assert "id" in result
    assert "student_id" in result
    assert "learning_objective_id" in result
    assert "rating" in result
    assert "learning_objective" in result
    
    # Check learning_objective structure
    lo_data = result["learning_objective"]
    assert "id" in lo_data
    assert "code" in lo_data
    assert "description" in lo_data
    assert "keywords" in lo_data
    assert "goal_short_name" in lo_data
    assert "strand" in lo_data
    assert "challenge" in lo_data


# ============================================================================
# Tests for GET endpoint: Classroom Metadata
# ============================================================================

def test_get_classroom_metadata_returns_all_fields(client, db_session):
    """Test that metadata endpoint returns all required fields."""
    classroom = _seed_classroom(db_session, "6")
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    assert "classroom_id" in result
    assert "classroom_name" in result
    assert "rating_levels" in result
    assert "strands" in result
    assert "challenges" in result
    assert "goal_short_names" in result


def test_get_classroom_metadata_rating_levels(client, db_session):
    """Test that all RatingLevel values are included."""
    classroom = _seed_classroom(db_session, "7")
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    rating_levels = result["rating_levels"]
    
    # Verify all expected rating levels
    expected_levels = [level.value for level in RatingLevel]
    assert set(rating_levels) == set(expected_levels)


def test_get_classroom_metadata_strands(client, db_session):
    """Test that all Strand values are included."""
    classroom = _seed_classroom(db_session, "8")
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    strands = result["strands"]
    
    # Verify all expected strands
    expected_strands = [strand.value for strand in Strand]
    assert set(strands) == set(expected_strands)


def test_get_classroom_metadata_challenges_filtered(client, db_session):
    """Test that challenges are filtered to classroom's learning objectives."""
    classroom = _seed_classroom(db_session, "9")
    
    # Create learning objectives
    lo_1 = _seed_learning_objective(db_session, classroom.id, "LO-CHAL-001")
    lo_2 = _seed_learning_objective(db_session, classroom.id, "LO-CHAL-002")
    
    # Create challenges
    challenge_1 = _seed_challenge(db_session, "Challenge 1", Semester.FIRST, [lo_1.id])
    challenge_2 = _seed_challenge(db_session, "Challenge 2", Semester.SECOND, [lo_2.id])
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    challenges = result["challenges"]
    
    # Verify both challenges are included
    assert len(challenges) == 2
    challenge_names = {c["name"] for c in challenges}
    assert "Challenge 1" in challenge_names
    assert "Challenge 2" in challenge_names


def test_get_classroom_metadata_goal_short_names(client, db_session):
    """Test that goal short names are included."""
    classroom = _seed_classroom(db_session, "10")
    
    # Create goal short names and learning objectives
    gsn_1 = GoalShortName(name="Goal 1", strand=Strand.CODING)
    gsn_2 = GoalShortName(name="Goal 2", strand=Strand.DESIGN)
    db_session.add_all([gsn_1, gsn_2])
    db_session.commit()
    db_session.refresh(gsn_1)
    db_session.refresh(gsn_2)
    
    lo_1 = LearningObjective(
        code="LO-GSN-001",
        description="Desc",
        keywords="kw",
        classroom_id=classroom.id,
        goal_short_name_id=gsn_1.id
    )
    lo_2 = LearningObjective(
        code="LO-GSN-002",
        description="Desc",
        keywords="kw",
        classroom_id=classroom.id,
        goal_short_name_id=gsn_2.id
    )
    db_session.add_all([lo_1, lo_2])
    db_session.commit()
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    goal_short_names = result["goal_short_names"]
    
    # Verify both goal short names are included
    assert len(goal_short_names) == 2
    gsn_names = {gsn["name"] for gsn in goal_short_names}
    assert "Goal 1" in gsn_names
    assert "Goal 2" in gsn_names


def test_get_classroom_metadata_empty_classroom(client, db_session):
    """Test metadata for classroom with no learning objectives."""
    classroom = _seed_classroom(db_session, "11")
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    
    # Verify basic fields exist
    assert result["classroom_id"] == classroom.id
    assert result["classroom_name"] == classroom.name
    
    # Verify rating levels and strands are still included
    assert len(result["rating_levels"]) > 0
    assert len(result["strands"]) > 0
    
    # Challenges and goal short names should be empty
    assert result["challenges"] == []
    assert result["goal_short_names"] == []


def test_get_classroom_metadata_nonexistent_classroom(client):
    """Test metadata for non-existent classroom."""
    response = client.get("/classrooms/99999/metadata")
    assert response.status_code == 404
    assert "Classroom not found" in response.json()["detail"]


def test_get_classroom_metadata_no_duplicate_goal_short_names(client, db_session):
    """Test that goal short names appear only once even if used by multiple LOs."""
    classroom = _seed_classroom(db_session, "12")
    
    # Create one goal short name
    gsn = GoalShortName(name="Shared Goal", strand=Strand.MARKETING)
    db_session.add(gsn)
    db_session.commit()
    db_session.refresh(gsn)
    
    # Create multiple learning objectives with the same goal short name
    for i in range(3):
        lo = LearningObjective(
            code=f"LO-DUP-{i:03d}",
            description="Desc",
            keywords="kw",
            classroom_id=classroom.id,
            goal_short_name_id=gsn.id
        )
        db_session.add(lo)
    db_session.commit()
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    goal_short_names = result["goal_short_names"]
    
    # Verify the goal short name appears exactly once
    assert len(goal_short_names) == 1
    assert goal_short_names[0]["name"] == "Shared Goal"


def test_get_classroom_metadata_challenge_details(client, db_session):
    """Test that challenge metadata includes correct details."""
    classroom = _seed_classroom(db_session, "13")
    
    lo = _seed_learning_objective(db_session, classroom.id, "LO-CHAL-DETAIL")
    challenge = _seed_challenge(
        db_session,
        "Capstone Challenge",
        Semester.THIRD,
        [lo.id]
    )
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    challenges = result["challenges"]
    
    assert len(challenges) == 1
    chal_data = challenges[0]
    assert chal_data["id"] == challenge.id
    assert chal_data["name"] == "Capstone Challenge"
    assert chal_data["semester"] == Semester.THIRD.value


def test_get_classroom_metadata_goal_short_name_details(client, db_session):
    """Test that goal short name metadata includes correct details."""
    classroom = _seed_classroom(db_session, "14")
    
    gsn = GoalShortName(name="Professional Skills", strand=Strand.PROFESSIONAL_SKILLS)
    db_session.add(gsn)
    db_session.commit()
    db_session.refresh(gsn)
    
    lo = LearningObjective(
        code="LO-GSN-DETAIL",
        description="Desc",
        keywords="kw",
        classroom_id=classroom.id,
        goal_short_name_id=gsn.id
    )
    db_session.add(lo)
    db_session.commit()
    
    response = client.get(f"/classrooms/{classroom.id}/metadata")
    assert response.status_code == 200
    
    result = response.json()
    goal_short_names = result["goal_short_names"]
    
    assert len(goal_short_names) == 1
    gsn_data = goal_short_names[0]
    assert gsn_data["id"] == gsn.id
    assert gsn_data["name"] == "Professional Skills"
    assert gsn_data["strand"] == Strand.PROFESSIONAL_SKILLS.value
