"""Integration tests for authentication and role-based authorization."""

import pytest
from starlette.testclient import TestClient


# PUBLIC AND AUTHENTICATED READS
# Root and health remain public. Resource reads require a valid token, and both
# demo roles may perform them.


def test_root_and_health_remain_public(client: TestClient) -> None:
    """The introductory endpoints do not require a Bearer token."""
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_protected_read_rejects_a_missing_token(client: TestClient) -> None:
    """A missing Bearer token receives 401 and the standard challenge header."""
    response = client.get("/projects")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid Bearer token"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_read_rejects_an_unknown_token(client: TestClient) -> None:
    """An unrecognized Bearer token is not treated as an authenticated user."""
    response = client.get(
        "/tasks",
        headers={"Authorization": "Bearer not-a-demo-token"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("path", ["/projects", "/tasks"])
def test_member_can_read_protected_collections(
    member_client: TestClient,
    path: str,
) -> None:
    """A member token permits safe resource reads."""
    response = member_client.get(path)

    assert response.status_code == 200
    assert response.json() == []


# ADMINISTRATOR-ONLY WRITES
# A member is authenticated but lacks the administrator role, so write routes
# return 403 before reaching request validation or the service layer.


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/projects", {"name": "Member Project", "description": "Denied."}),
        ("PUT", "/projects/999999", {"name": "Member Project", "description": "Denied."}),
        ("DELETE", "/projects/999999", None),
        (
            "POST",
            "/tasks",
            {
                "title": "Member Task",
                "description": "Denied.",
                "completed": False,
                "project_id": 999999,
            },
        ),
        (
            "PUT",
            "/tasks/999999",
            {
                "title": "Member Task",
                "description": "Denied.",
                "completed": False,
                "project_id": 999999,
            },
        ),
        ("DELETE", "/tasks/999999", None),
    ],
)
def test_member_cannot_use_administrator_only_write_routes(
    member_client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, object] | None,
) -> None:
    """Every Project and Task write operation requires the administrator role."""
    response = member_client.request(
        method,
        path,
        json=json_body,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Administrator role required"}


def test_administrator_can_complete_a_project_and_task_write_workflow(
    admin_client: TestClient,
) -> None:
    """An admin token reaches the existing CRUD workflow after authorization."""
    project_response = admin_client.post(
        "/projects",
        json={"name": "Authorized Project", "description": "Created by an admin."},
    )
    assert project_response.status_code == 201
    project = project_response.json()

    task_response = admin_client.post(
        "/tasks",
        json={
            "title": "Authorized Task",
            "description": "Created by an admin.",
            "completed": False,
            "project_id": project["id"],
        },
    )
    assert task_response.status_code == 201
    task = task_response.json()

    replace_response = admin_client.put(
        f"/tasks/{task['id']}",
        json={
            "title": "Completed Task",
            "description": "Updated by an admin.",
            "completed": True,
            "project_id": project["id"],
        },
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["completed"] is True

    assert admin_client.delete(f"/tasks/{task['id']}").status_code == 204
    assert admin_client.delete(f"/projects/{project['id']}").status_code == 204
