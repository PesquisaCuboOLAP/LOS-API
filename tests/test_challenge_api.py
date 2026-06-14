from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName, Strand
from app.models.learning_objective import LearningObjective


def _seed_learning_objective(db_session, suffix: str) -> LearningObjective:
    classroom = Classroom(
        name=f"202{suffix}-202{int(suffix) + 1}",
        start_year=f"202{suffix}",
        end_year=f"202{int(suffix) + 1}",
    )
    goal_short_name = GoalShortName(
        name=f"Goal {suffix}",
        strand=Strand.CODING,
    )
    db_session.add_all([classroom, goal_short_name])
    db_session.commit()
    db_session.refresh(classroom)
    db_session.refresh(goal_short_name)

    learning_objective = LearningObjective(
        code=f"LO-{suffix}",
        description=f"Description {suffix}",
        keywords=f"keyword-{suffix}",
        classroom_id=classroom.id,
        goal_short_name_id=goal_short_name.id,
    )
    db_session.add(learning_objective)
    db_session.commit()
    db_session.refresh(learning_objective)
    return learning_objective


def test_challenge_crud_flow(client, db_session):
    learning_objective_one = _seed_learning_objective(db_session, "4")
    learning_objective_two = _seed_learning_objective(db_session, "6")

    create_response = client.post(
        "/challenges",
        json={
            "name": "Capstone",
            "semester": 2,
            "learning_objective_ids": [
                learning_objective_one.id,
                learning_objective_two.id,
            ],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Capstone"
    assert created["semester"] == 2
    assert created["learning_objective_ids"] == [
        learning_objective_one.id,
        learning_objective_two.id,
    ]

    challenge_id = created["id"]

    list_response = client.get("/challenges")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [challenge_id]

    get_response = client.get(f"/challenges/{challenge_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == challenge_id

    update_response = client.put(
        f"/challenges/{challenge_id}",
        json={
            "name": "Capstone Revised",
            "semester": 3,
            "learning_objective_ids": [learning_objective_two.id],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Capstone Revised"
    assert updated["semester"] == 3
    assert updated["learning_objective_ids"] == [learning_objective_two.id]

    delete_response = client.delete(f"/challenges/{challenge_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/challenges/{challenge_id}")
    assert missing_response.status_code == 404


def test_challenge_create_rejects_missing_learning_objective_ids(client):
    response = client.post(
        "/challenges",
        json={
            "name": "Broken Challenge",
            "semester": 1,
            "learning_objective_ids": [999, 1000],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "missing_learning_objective_ids": [999, 1000]
    }