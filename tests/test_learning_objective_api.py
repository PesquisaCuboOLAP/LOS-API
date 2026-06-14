import pytest

from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName, Strand


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