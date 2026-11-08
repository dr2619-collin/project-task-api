"""Integration tests for Problem Details errors and the /api/v1 migration."""

from typing import Any

import pytest
from starlette.testclient import TestClient


@pytest.mark.parametrize(
    ("path", "problem_type"),
    [
        ("/api/v1/projects/999999", "project-not-found"),
        ("/api/v1/tasks/999999", "task-not-found"),
    ],
)
def test_missing_resources_return_problem_details(
    database_client: TestClient,
    admin_headers: dict[str, str],
    path: str,
    problem_type: str,
) -> None:
    response = database_client.get(path, headers=admin_headers)

    assert_problem(response, 404, problem_type, path)


def test_project_with_tasks_returns_a_conflict_problem(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    project = create_project(database_client, admin_headers, "/api/v1")
    create_task(database_client, admin_headers, "/api/v1", project["id"])
    path = f"/api/v1/projects/{project['id']}"

    response = database_client.delete(path, headers=admin_headers)

    assert_problem(response, 409, "project-has-tasks", path)


def test_authentication_and_authorization_failures_use_problem_details(
    database_client: TestClient,
    member_headers: dict[str, str],
) -> None:
    unauthorized = database_client.get("/api/v1/projects")
    forbidden = database_client.post(
        "/api/v1/projects",
        json={"name": "Denied", "description": "A member cannot create this."},
        headers=member_headers,
    )

    assert_problem(unauthorized, 401, "unauthorized", "/api/v1/projects")
    assert unauthorized.headers["www-authenticate"] == "Bearer"
    assert_problem(forbidden, 403, "forbidden", "/api/v1/projects")


@pytest.mark.parametrize(
    "path",
    ["/api/v1/projects/not-an-integer", "/async-demo/async-wait?seconds=4"],
)
def test_path_and_query_validation_use_problem_details(
    database_client: TestClient,
    admin_headers: dict[str, str],
    path: str,
) -> None:
    response = database_client.get(path, headers=admin_headers)

    assert_problem(response, 422, "validation-error", path.split("?")[0])
    assert response.json()["errors"]


def test_body_validation_uses_problem_details(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = database_client.post(
        "/api/v1/projects", json={"name": "Incomplete"}, headers=admin_headers
    )

    assert_problem(response, 422, "validation-error", "/api/v1/projects")
    assert response.json()["errors"]


def test_unexpected_error_does_not_expose_internal_details(
    reset_database: None,
) -> None:
    from app.main import app

    def raise_for_test() -> None:
        raise RuntimeError("internal test failure must not reach the client")

    app.add_api_route("/_test/unexpected-error", raise_for_test, include_in_schema=False)
    try:
        with TestClient(app, raise_server_exceptions=False) as error_client:
            response = error_client.get("/_test/unexpected-error")
    finally:
        app.router.routes.pop()

    assert_problem(response, 500, "internal-server-error", "/_test/unexpected-error")
    assert "internal test failure" not in response.text


def test_legacy_path_remains_available_and_advertises_successor(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = database_client.get("/projects", headers=admin_headers)

    assert response.status_code == 200
    assert response.headers["deprecation"] == "true"
    assert response.headers["sunset"] == "Wed, 09 Dec 2026 06:00:00 GMT"
    assert response.headers["link"] == '</api/v1/projects>; rel="successor-version"'


def test_versioned_path_has_same_behavior_without_legacy_headers(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = database_client.get("/api/v1/projects", headers=admin_headers)

    assert response.status_code == 200
    assert "deprecation" not in response.headers
    assert "sunset" not in response.headers
    assert "link" not in response.headers


def test_versioned_project_and_task_workflow(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    project = create_project(database_client, admin_headers, "/api/v1")
    assert database_client.get(
        f"/api/v1/projects/{project['id']}", headers=admin_headers
    ).status_code == 200

    task = create_task(database_client, admin_headers, "/api/v1", project["id"])
    replace_response = database_client.put(
        f"/api/v1/tasks/{task['id']}",
        json={
            "title": "Completed Task",
            "description": "Updated through the versioned API.",
            "completed": True,
            "project_id": project["id"],
        },
        headers=admin_headers,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["completed"] is True
    assert database_client.delete(
        f"/api/v1/tasks/{task['id']}", headers=admin_headers
    ).status_code == 204
    assert database_client.delete(
        f"/api/v1/projects/{project['id']}", headers=admin_headers
    ).status_code == 204


def test_openapi_documents_versioned_paths_and_problem_responses(
    database_client: TestClient,
) -> None:
    paths = database_client.get("/openapi.json").json()["paths"]

    assert paths["/projects"]["get"]["deprecated"] is True
    assert paths["/api/v1/projects"]["get"].get("deprecated") is not True
    missing_project = paths["/api/v1/projects/{project_id}"]["get"]["responses"]["404"]
    invalid_project = paths["/api/v1/projects"]["post"]["responses"]["422"]
    assert "application/problem+json" in missing_project["content"]
    assert "application/problem+json" in invalid_project["content"]


def assert_problem(response, status_code: int, problem_type: str, instance: str) -> None:
    """Check the shared Problem Details fields for a client-visible error."""
    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("application/problem+json")
    body: dict[str, Any] = response.json()
    assert {"type", "title", "status", "detail", "instance"} <= set(body)
    assert body["type"].endswith(f"/{problem_type}")
    assert body["status"] == status_code
    assert body["instance"] == instance


def create_project(
    client: TestClient,
    headers: dict[str, str],
    prefix: str,
) -> dict[str, Any]:
    response = client.post(
        f"{prefix}/projects",
        json={"name": "Protected Project", "description": "Has a related Task."},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_task(
    client: TestClient,
    headers: dict[str, str],
    prefix: str,
    project_id: int,
) -> dict[str, Any]:
    response = client.post(
        f"{prefix}/tasks",
        json={
            "title": "Protected Task",
            "description": "Prevents the Project from being deleted.",
            "completed": False,
            "project_id": project_id,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()
