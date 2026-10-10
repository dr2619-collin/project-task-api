"""In-memory router integration tests for the Project resource."""

from starlette.testclient import TestClient


def test_project_crud_works_with_memory_client(memory_client: TestClient) -> None:
    """The Project router works when DI selects the in-memory service."""
    create_response = memory_client.post(
        "/projects",
        json={
            "name": "Memory Project",
            "description": "Stored by the in-memory service.",
        },
    )

    assert create_response.status_code == 201
    project = create_response.json()

    get_response = memory_client.get(f"/projects/{project['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == project

    replace_response = memory_client.put(
        f"/projects/{project['id']}",
        json={
            "name": "Updated Memory Project",
            "description": "Updated without PostgreSQL.",
        },
    )
    assert replace_response.status_code == 200

    delete_response = memory_client.delete(f"/projects/{project['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert memory_client.get("/projects").json() == []


def test_project_tasks_route_works_with_memory_client(
    memory_client: TestClient,
) -> None:
    """The memory services preserve the Project-to-Task relationship."""
    project = create_project(memory_client)
    task_response = memory_client.post(
        "/tasks",
        json={
            "title": "Memory Task",
            "description": "Related to an in-memory project.",
            "completed": False,
            "project_id": project["id"],
        },
    )
    assert task_response.status_code == 201

    response = memory_client.get(f"/projects/{project['id']}/tasks")

    assert response.status_code == 200
    assert response.json() == [task_response.json()]


def create_project(memory_client: TestClient) -> dict:
    """Create one Project through the memory-backed public API."""
    response = memory_client.post(
        "/projects",
        json={
            "name": "Memory Parent",
            "description": "Parent project for the memory router test.",
        },
    )
    assert response.status_code == 201
    return response.json()
