"""Successful-path integration tests for every Task API endpoint."""

from starlette.testclient import TestClient


def test_create_list_and_get_tasks(client: TestClient) -> None:
    """POST, GET collection, and GET item work together for Tasks."""
    project = create_project(client, "Course API")
    first_task = create_task(client, project["id"], "First Task")
    second_task = create_task(client, project["id"], "Second Task")

    list_response = client.get("/tasks")

    assert list_response.status_code == 200
    assert list_response.json() == [first_task, second_task]

    get_response = client.get(f"/tasks/{first_task['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == first_task


def test_replace_task_updates_the_public_resource(client: TestClient) -> None:
    """PUT replaces Task fields and can assign an existing replacement Project."""
    original_project = create_project(client, "Original Project")
    replacement_project = create_project(client, "Replacement Project")
    task = create_task(client, original_project["id"], "Original Task")

    replace_response = client.put(
        f"/tasks/{task['id']}",
        json={
            "title": "Updated Task",
            "description": "Updated through the API.",
            "completed": True,
            "project_id": replacement_project["id"],
        },
    )

    assert replace_response.status_code == 200
    updated_task = replace_response.json()
    assert updated_task == {
        "id": task["id"],
        "title": "Updated Task",
        "description": "Updated through the API.",
        "completed": True,
        "project_id": replacement_project["id"],
    }

    get_response = client.get(f"/tasks/{task['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_task


def test_delete_task_removes_the_public_resource(client: TestClient) -> None:
    """DELETE returns no content and removes a Task from its collection."""
    project = create_project(client, "Course API")
    task = create_task(client, project["id"], "Deleted Task")

    delete_response = client.delete(f"/tasks/{task['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    list_response = client.get("/tasks")
    assert list_response.status_code == 200
    assert list_response.json() == []


# HELPERS


def create_project(client: TestClient, name: str) -> dict:
    """Create a parent Project needed by a Task request."""
    response = client.post(
        "/projects",
        json={
            "name": name,
            "description": f"Description for {name}.",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_task(client: TestClient, project_id: int, title: str) -> dict:
    """Create one Task through the public API and return its response body."""
    response = client.post(
        "/tasks",
        json={
            "title": title,
            "description": f"Description for {title}.",
            "completed": False,
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    return response.json()
