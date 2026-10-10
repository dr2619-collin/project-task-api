"""In-memory router integration tests for the Task resource."""

from starlette.testclient import TestClient


def test_task_crud_works_with_memory_client(memory_client: TestClient) -> None:
    """The Task router works when DI selects the in-memory service."""
    project = create_project(memory_client)
    create_response = memory_client.post(
        "/tasks",
        json={
            "title": "Memory Task",
            "description": "Stored by the in-memory service.",
            "completed": False,
            "project_id": project["id"],
        },
    )

    assert create_response.status_code == 201
    task = create_response.json()

    get_response = memory_client.get(f"/tasks/{task['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == task

    replace_response = memory_client.put(
        f"/tasks/{task['id']}",
        json={
            "title": "Updated Memory Task",
            "description": "Updated without PostgreSQL.",
            "completed": True,
            "project_id": project["id"],
        },
    )
    assert replace_response.status_code == 200

    delete_response = memory_client.delete(f"/tasks/{task['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert memory_client.get("/tasks").json() == []


def create_project(memory_client: TestClient) -> dict:
    """Create the parent Project required by a Task request."""
    response = memory_client.post(
        "/projects",
        json={
            "name": "Memory Task Parent",
            "description": "Parent project for the memory task test.",
        },
    )
    assert response.status_code == 201
    return response.json()
