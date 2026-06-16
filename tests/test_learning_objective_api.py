import pytest

from app.models.challenge import Challenge, Semester
from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName, Strand
from app.models.learning_objective import LearningObjective


def _seed_classroom(db_session) -> Classroom:
    classroom = Classroom(name="2024-2025", start_year="2024", end_year="2025")
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom


def _seed_goal_short_name(db_session) -> GoalShortName:
    goal_short_name = GoalShortName(name="Analysis", strand=Strand.CODING)
    db_session.add(goal_short_name)
    db_session.commit()
    db_session.refresh(goal_short_name)
    return goal_short_name


def test_learning_objective_crud_and_classroom_listing(client, db_session):
    classroom = _seed_classroom(db_session)
    goal_short_name = _seed_goal_short_name(db_session)

    create_response = client.post(
        "/learning-objectives",
        json={
            "code": "LO-100",
            "description": "Build an API",
            "keywords": "api, fastapi",
            "goal_short_name_id": goal_short_name.id,
            "classroom_id": classroom.id,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["code"] == "LO-100"
    assert created["goal_short_name_id"] == goal_short_name.id
    assert created["classroom_id"] == classroom.id

    learning_objective_id = created["id"]

    get_response = client.get(f"/learning-objectives/{learning_objective_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == learning_objective_id

    classroom_list_response = client.get(
        f"/classrooms/{classroom.id}/learning-objectives"
    )
    assert classroom_list_response.status_code == 200
    assert [item["id"] for item in classroom_list_response.json()] == [learning_objective_id]

    update_response = client.put(
        f"/learning-objectives/{learning_objective_id}",
        json={
            "code": "LO-101",
            "description": "Ship the API",
            "keywords": "release, api",
            "goal_short_name_id": goal_short_name.id,
            "classroom_id": classroom.id,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["code"] == "LO-101"
    assert updated["description"] == "Ship the API"

    delete_response = client.delete(f"/learning-objectives/{learning_objective_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/learning-objectives/{learning_objective_id}")
    assert missing_response.status_code == 404


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        (
            {
                "code": "LO-200",
                "description": "Missing classroom",
                "keywords": "missing, classroom",
                "goal_short_name_id": 1,
                "classroom_id": 999,
            },
            "Classroom not found",
        ),
        (
            {
                "code": "LO-201",
                "description": "Missing goal short name",
                "keywords": "missing, goal",
                "goal_short_name_id": 999,
                "classroom_id": 1,
            },
            "Goal short name not found",
        ),
    ],
)
def test_learning_objective_create_validates_related_entities(
    client,
    db_session,
    payload,
    expected_detail,
):
    classroom = _seed_classroom(db_session)
    goal_short_name = _seed_goal_short_name(db_session)

    if payload["classroom_id"] == 1:
        payload = {**payload, "classroom_id": classroom.id}
    if payload["goal_short_name_id"] == 1:
        payload = {**payload, "goal_short_name_id": goal_short_name.id}

    response = client.post("/learning-objectives", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail


def test_import_learning_objectives_creates_missing_goal_short_names_and_updates_challenges(
    client,
    db_session,
):
    classroom = _seed_classroom(db_session)
    existing_goal_short_name = GoalShortName(name="Business", strand=Strand.MARKETING)
    existing_challenge = Challenge(
        name="Produto IA",
        semester=Semester.FIRST,
        learning_objective_ids=[],
    )
    db_session.add_all([existing_goal_short_name, existing_challenge])
    db_session.commit()

    csv_content = "\n".join(
        [
            "Code,Learning Strand,Goal Short Name,Learning Objective,Learning Objective Keywords,Challenge",
            "MK-BUS-001,Marketing,Business,Forecast team expenses,Cost AI,Residência",
            "MK-APP-001,Marketing,App Store,Write product metadata,Metadata,Produto IA",
        ]
    )

    response = client.post(
        f"/classrooms/{classroom.id}/learning-objectives/import/1",
        files={"file": ("learning-objectives.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 201
    summary = response.json()
    assert summary == {
        "classroom_id": classroom.id,
        "semester": 1,
        "total_rows": 2,
        "imported_goal_short_names": 1,
        "reused_goal_short_names": 1,
        "imported_learning_objectives": 2,
        "skipped_duplicate_learning_objectives": 0,
        "skipped_duplicate_rows_in_file": 0,
        "created_challenges": 1,
        "updated_challenges": 1,
        "skipped_empty_rows": 0,
    }

    goal_short_names = db_session.query(GoalShortName).order_by(GoalShortName.name.asc()).all()
    assert [(item.name, item.strand) for item in goal_short_names] == [
        ("App Store", Strand.MARKETING),
        ("Business", Strand.MARKETING),
    ]

    learning_objectives = (
        db_session.query(LearningObjective)
        .filter(LearningObjective.classroom_id == classroom.id)
        .order_by(LearningObjective.code.asc())
        .all()
    )
    assert [item.code for item in learning_objectives] == ["MK-APP-001", "MK-BUS-001"]

    produto_ia = db_session.query(Challenge).filter(Challenge.name == "Produto IA").first()
    residencia = db_session.query(Challenge).filter(Challenge.name == "Residência").first()

    assert produto_ia is not None
    assert produto_ia.semester == Semester.FIRST
    assert produto_ia.learning_objective_ids == [
        next(item.id for item in learning_objectives if item.code == "MK-APP-001")
    ]

    assert residencia is not None
    assert residencia.semester == Semester.FIRST
    assert residencia.learning_objective_ids == [
        next(item.id for item in learning_objectives if item.code == "MK-BUS-001")
    ]


def test_import_learning_objectives_is_idempotent_for_existing_codes(client, db_session):
    classroom = _seed_classroom(db_session)

    csv_content = "\n".join(
        [
            "Code,Learning Strand,Goal Short Name,Learning Objective,Learning Objective Keywords,Challenge",
            "MK-BUS-001,Marketing,Business,Forecast team expenses,Cost AI,Residência",
            "MK-APP-001,Marketing,App Store,Write product metadata,Metadata,Produto IA",
        ]
    )

    first_response = client.post(
        f"/classrooms/{classroom.id}/learning-objectives/import/1",
        files={"file": ("learning-objectives.csv", csv_content, "text/csv")},
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/classrooms/{classroom.id}/learning-objectives/import/1",
        files={"file": ("learning-objectives.csv", csv_content, "text/csv")},
    )

    assert second_response.status_code == 201
    summary = second_response.json()
    assert summary["imported_learning_objectives"] == 0
    assert summary["skipped_duplicate_learning_objectives"] == 2
    assert summary["created_challenges"] == 0
    assert summary["updated_challenges"] == 0

    learning_objectives = (
        db_session.query(LearningObjective)
        .filter(LearningObjective.classroom_id == classroom.id)
        .all()
    )
    assert len(learning_objectives) == 2

    produto_ia = db_session.query(Challenge).filter(Challenge.name == "Produto IA").first()
    residencia = db_session.query(Challenge).filter(Challenge.name == "Residência").first()
    assert produto_ia is not None
    assert residencia is not None
    assert len(produto_ia.learning_objective_ids) == 1
    assert len(residencia.learning_objective_ids) == 1


def test_import_learning_objectives_rejects_challenge_semester_conflicts(client, db_session):
    classroom = _seed_classroom(db_session)
    challenge = Challenge(
        name="Produto IA",
        semester=Semester.SECOND,
        learning_objective_ids=[],
    )
    db_session.add(challenge)
    db_session.commit()

    csv_content = "\n".join(
        [
            "Code,Learning Strand,Goal Short Name,Learning Objective,Learning Objective Keywords,Challenge",
            "MK-APP-001,Marketing,App Store,Write product metadata,Metadata,Produto IA",
        ]
    )

    response = client.post(
        f"/classrooms/{classroom.id}/learning-objectives/import/1",
        files={"file": ("learning-objectives.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Challenge already exists with a different semester: Produto IA"


def test_import_learning_objectives_rejects_invalid_learning_strands(client, db_session):
    classroom = _seed_classroom(db_session)

    csv_content = "\n".join(
        [
            "Code,Learning Strand,Goal Short Name,Learning Objective,Learning Objective Keywords,Challenge",
            "MK-APP-001,Unknown,App Store,Write product metadata,Metadata,Produto IA",
        ]
    )

    response = client.post(
        f"/classrooms/{classroom.id}/learning-objectives/import/1",
        files={"file": ("learning-objectives.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid learning strand at row 2: Unknown"