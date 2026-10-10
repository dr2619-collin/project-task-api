"""Successful-path integration tests for every Project API endpoint."""

from starlette.testclient import TestClient


def test_create_list_and_get_projects(database_client: TestClient) -> None:
    """POST, GET collection, and GET item work together for Projects."""
    first_project = create_project(database_client, "First Project")
    second_project = create_project(database_client, "Second Project")

    list_response = database_client.get("/projects")

    assert list_response.status_code == 200
    assert list_response.json() == [first_project, second_project]

    get_response = database_client.get(f"/projects/{first_project['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == first_project


def test_replace_project_updates_the_public_resource(database_client: TestClient) -> None:
    """PUT replaces a Project and later GET returns the new values."""
    project = create_project(database_client, "Original Project")

    replace_response = database_client.put(
        f"/projects/{project['id']}",
        json={
            "name": "Updated Project",
            "description": "Updated through the API.",
        },
    )

    assert replace_response.status_code == 200
    updated_project = replace_response.json()
    assert updated_project == {
        "id": project["id"],
        "name": "Updated Project",
        "description": "Updated through the API.",
    }

    get_response = database_client.get(f"/projects/{project['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_project


def test_delete_project_removes_the_public_resource(database_client: TestClient) -> None:
    """DELETE returns no content and removes a Project from its collection."""
    project = create_project(database_client, "Deleted Project")

    delete_response = database_client.delete(f"/projects/{project['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    list_response = database_client.get("/projects")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_list_project_tasks_returns_related_tasks(database_client: TestClient) -> None:
    """The related-resource endpoint returns Tasks for the requested Project."""
    project = create_project(database_client, "Course API")

    first_task_response = database_client.post(
        "/tasks",
        json={
            "title": "First Task",
            "description": "First related Task.",
            "completed": False,
            "project_id": project["id"],
        },
    )
    second_task_response = database_client.post(
        "/tasks",
        json={
            "title": "Second Task",
            "description": "Second related Task.",
            "completed": True,
            "project_id": project["id"],
        },
    )
    assert first_task_response.status_code == 201
    assert second_task_response.status_code == 201

    response = database_client.get(f"/projects/{project['id']}/tasks")

    assert response.status_code == 200
    assert response.json() == [first_task_response.json(), second_task_response.json()]


# HELPERS


def create_project(database_client: TestClient, name: str) -> dict:
    """Create one Project through the public API and return its response body."""
    response = database_client.post(
        "/projects",
        json={
            "name": name,
            "description": f"Description for {name}.",
        },
    )
    assert response.status_code == 201
    return response.json()
