"""Negative API tests for invalid, missing, and disallowed client requests."""

import pytest
from starlette.testclient import TestClient


# REQUEST-BODY VALIDATION
# FastAPI passes JSON bodies to Pydantic before the route handler completes.
# These tests verify required fields, unknown fields, and field boundaries.


def test_create_project_rejects_missing_required_field(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    """A request without the required description is rejected with 422."""
    response = database_client.post(
        "/projects", json={"name": "Incomplete Project"}, headers=admin_headers
    )

    assert_validation_error(response)


def test_create_project_rejects_undocumented_field(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    """extra='forbid' prevents a client from sending an unknown JSON field."""
    response = database_client.post(
        "/projects",
        json={
            "name": "Unexpected Field",
            "description": "This request includes a field outside the contract.",
            "owner": "Undocumented client value",
        },
        headers=admin_headers,
    )

    assert_validation_error(response)


# REQUEST-BODY BOUNDARY VALIDATION
# These values have the expected JSON fields but violate Pydantic constraints.


@pytest.mark.parametrize(
    ("name", "description"),
    [
        ("   ", "A blank name becomes invalid after whitespace stripping."),
        ("x" * 101, "The project name exceeds its documented maximum length."),
    ],
    ids=["blank-name", "name-over-maximum"],
)
def test_create_project_rejects_invalid_boundary_values(
    database_client: TestClient,
    admin_headers: dict[str, str],
    name: str,
    description: str,
) -> None:
    """Pydantic enforces documented Project name boundaries over HTTP."""
    response = database_client.post(
        "/projects",
        json={"name": name, "description": description},
        headers=admin_headers,
    )

    assert_validation_error(response)


# PATH-PARAMETER VALIDATION
# FastAPI validates the typed `int` path parameters before it calls a route.


@pytest.mark.parametrize(
    "path",
    ["/projects/not-an-integer", "/tasks/not-an-integer"],
    ids=["project-id", "task-id"],
)
def test_typed_path_parameters_reject_wrong_data_type(
    database_client: TestClient,
    admin_headers: dict[str, str],
    path: str,
) -> None:
    """FastAPI rejects a non-integer resource identifier before the route runs."""
    response = database_client.get(path, headers=admin_headers)

    assert_validation_error(response)


# RESOURCE AND BUSINESS-RULE REJECTIONS
# These requests have a valid shape, so the application layers decide whether
# the requested resource or relationship is allowed and return 404 or 409.


@pytest.mark.parametrize(
    "path",
    ["/projects/999999", "/tasks/999999"],
    ids=["project", "task"],
)
def test_missing_resources_return_not_found(
    database_client: TestClient,
    admin_headers: dict[str, str],
    path: str,
) -> None:
    """A valid identifier with no matching resource returns the documented 404."""
    response = database_client.get(path, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"]


def test_create_task_rejects_nonexistent_parent_project(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    """The Task relationship rule becomes a client-visible 404 response."""
    response = database_client.post(
        "/tasks",
        json={
            "title": "Orphan Task",
            "description": "Its referenced Project does not exist.",
            "completed": False,
            "project_id": 999999,
        },
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"]


def test_delete_project_rejects_project_with_related_tasks(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    """A Project with Tasks remains protected by the documented 409 conflict."""
    project = create_project(database_client, admin_headers)
    create_task(database_client, admin_headers, project["id"])

    response = database_client.delete(
        f"/projects/{project['id']}", headers=admin_headers
    )

    assert response.status_code == 409
    assert response.json()["detail"]


# HELPERS


def assert_validation_error(response) -> None:
    """Check FastAPI's stable 422 status and validation-error response shape."""
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail


def create_project(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> dict:
    """Create a Project needed by the deletion-conflict negative test."""
    response = database_client.post(
        "/projects",
        json={"name": "Protected Project", "description": "Has a related Task."},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def create_task(
    database_client: TestClient,
    admin_headers: dict[str, str],
    project_id: int,
) -> dict:
    """Create a related Task that makes the Project deletion invalid."""
    response = database_client.post(
        "/tasks",
        json={
            "title": "Protected Task",
            "description": "Prevents the Project from being deleted.",
            "completed": False,
            "project_id": project_id,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()
