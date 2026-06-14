from app.models.classroom import Classroom
from app.models.goal_short_name import GoalShortName, Strand
from app.models.learning_objective import LearningObjective


def test_goal_short_name_crud_flow(client):
    create_response = client.post(
        "/goal-short-names",
        json={"name": "Communication", "strand": "CODING"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Communication"
    assert created["strand"] == "CODING"

    list_response = client.get("/goal-short-names")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    goal_short_name_id = created["id"]

    get_response = client.get(f"/goal-short-names/{goal_short_name_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == goal_short_name_id

    update_response = client.put(
        f"/goal-short-names/{goal_short_name_id}",
        json={"name": "Storytelling", "strand": "DESIGN"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Storytelling"
    assert updated["strand"] == "DESIGN"

    delete_response = client.delete(f"/goal-short-names/{goal_short_name_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/goal-short-names/{goal_short_name_id}")
    assert missing_response.status_code == 404


def test_delete_goal_short_name_blocks_when_linked_to_learning_objective(client, db_session):
    classroom = Classroom(name="2024-2025", start_year="2024", end_year="2025")
    goal_short_name = GoalShortName(name="Research", strand=Strand.PROCESS)
    db_session.add_all([classroom, goal_short_name])
    db_session.commit()
    db_session.refresh(classroom)
    db_session.refresh(goal_short_name)

    learning_objective = LearningObjective(
        code="LO-1",
        description="Research a topic",
        keywords="research, planning",
        classroom_id=classroom.id,
        goal_short_name_id=goal_short_name.id,
    )
    db_session.add(learning_objective)
    db_session.commit()

    response = client.delete(f"/goal-short-names/{goal_short_name.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot delete a goal short name with linked learning objectives"