"""Conformance tests for the public OpenAPI contract.

These tests begin from what an API consumer can see: `/openapi.json`, response
status codes, and JSON bodies. They supplement—not replace—the Module 06
integration tests that exercise successful workflows in detail.
"""

from typing import Any

import pytest
import schemathesis
from openapi_spec_validator import validate
from starlette.testclient import TestClient


# OPENAPI DOCUMENT VALIDATION


# OPENAPI-SPEC-VALIDATOR TEST
# This is the one direct use of openapi-spec-validator in this project. It
# checks whether the complete generated OpenAPI document is structurally valid.
def test_generated_openapi_document_is_valid(client: TestClient) -> None:
    """The API publishes a structurally valid OpenAPI document."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_document = response.json()
    # The validator raises an exception if FastAPI generated an invalid OpenAPI
    # document. It validates the complete document, not a single data schema.
    validate(openapi_document)


# APPROVED CONTRACT ASSERTIONS
# These ordinary pytest tests protect the paths, methods, status codes, and
# component schemas that API consumers are expected to depend on.


def test_openapi_document_declares_the_approved_public_operations(
    client: TestClient,
) -> None:
    """Required paths, methods, and successful/error outcomes stay published."""
    openapi_document = client.get("/openapi.json").json()
    paths = openapi_document["paths"]

    expected_statuses = {
        "/": {"get": {"200"}},
        "/health": {"get": {"200"}},
        "/projects": {"get": {"200"}, "post": {"201", "422"}},
        "/projects/{project_id}": {
            "get": {"200", "404", "422"},
            "put": {"200", "404", "422"},
            "delete": {"204", "404", "409", "422"},
        },
        "/projects/{project_id}/tasks": {"get": {"200", "404", "422"}},
        "/tasks": {"get": {"200"}, "post": {"201", "404", "422"}},
        "/tasks/{task_id}": {
            "get": {"200", "404", "422"},
            "put": {"200", "404", "422"},
            "delete": {"204", "404", "422"},
        },
    }

    for path, operations in expected_statuses.items():
        assert path in paths
        for method, statuses in operations.items():
            assert method in paths[path]
            documented_statuses = set(paths[path][method]["responses"])
            assert statuses <= documented_statuses


def test_openapi_document_describes_project_and_task_schemas(
    client: TestClient,
) -> None:
    """Pydantic request and response rules appear in the public contract."""
    openapi_document = client.get("/openapi.json").json()
    schemas = openapi_document["components"]["schemas"]

    assert_schema_fields(schemas["ProjectCreate"], {"name", "description"})
    assert_schema_fields(schemas["ProjectResponse"], {"id", "name", "description"})
    assert_schema_fields(
        schemas["TaskCreate"],
        {"title", "description", "completed", "project_id"},
    )
    assert_schema_fields(
        schemas["TaskResponse"],
        {"id", "title", "description", "completed", "project_id"},
    )

    project_name = schemas["ProjectCreate"]["properties"]["name"]
    assert project_name["type"] == "string"
    assert project_name["minLength"] == 1
    assert project_name["maxLength"] == 100
    assert schemas["TaskCreate"]["properties"]["completed"]["default"] is False

    project_post_schema = paths_response_schema(
        openapi_document,
        "/projects",
        "post",
        "201",
    )
    task_post_schema = paths_response_schema(
        openapi_document,
        "/tasks",
        "post",
        "201",
    )
    assert project_post_schema == {"$ref": "#/components/schemas/ProjectResponse"}
    assert task_post_schema == {"$ref": "#/components/schemas/TaskResponse"}


# TARGETED RESPONSE CONFORMANCE
# These ordinary pytest tests send known requests and confirm their visible
# HTTP behavior matches the important outcomes documented by the API.


def test_create_project_matches_its_documented_public_response(
    client: TestClient,
) -> None:
    """A created Project has the documented status and response shape."""
    response = client.post(
        "/projects",
        json={
            "name": "Contract Test Project",
            "description": "Verify the documented Project response.",
        },
    )

    assert response.status_code == 201
    project = response.json()
    assert set(project) == {"id", "name", "description"}
    assert isinstance(project["id"], int)
    assert project["id"] > 0
    assert project["name"] == "Contract Test Project"
    assert project["description"] == "Verify the documented Project response."


def test_missing_project_matches_documented_not_found_response(
    client: TestClient,
) -> None:
    """A consumer receives the documented 404 outcome for a missing Project."""
    response = client.get("/projects/999999")

    assert response.status_code == 404
    assert response.json()["detail"]


def test_project_with_tasks_matches_documented_conflict_response(
    client: TestClient,
) -> None:
    """Deleting a Project with Tasks returns the documented 409 outcome."""
    project = create_project(client)
    create_task(client, project["id"])

    response = client.delete(f"/projects/{project['id']}")

    assert response.status_code == 409
    assert response.json()["detail"]


# SCHEMA-DRIVEN TESTING WITH SCHEMATHESIS


@pytest.fixture
def openapi_schema(client: TestClient) -> Any:
    """Load the contract only after the isolated API is running."""
    # Importing the application only after requesting `client` preserves the
    # Module 06 fixture order: DATABASE_URL already points to Testcontainers.
    from app.main import app

    return schemathesis.openapi.from_asgi("/openapi.json", app)


# SCHEMATHESIS / PYTEST CONNECTION
#
# `openapi_schema` above is a normal pytest fixture. This lazy `schema` object
# tells Schemathesis to request that fixture later, when pytest is running a
# test—not while Python is importing this file. That preserves the Module 06
# setup order, where `client` first points DATABASE_URL at Testcontainers.
#
# The .include(...) call then limits generated tests to three safe GET routes.
schema = schemathesis.pytest.from_fixture("openapi_schema").include(
    method="GET",
    path_regex=r"^/(health|projects|tasks)$",
)


# `@schema.parametrize()` connects this test function to the lazy schema
# above. Schemathesis resolves `openapi_schema`, creates one `case` argument
# for each selected OpenAPI operation, and runs this function once per case.
# `case` is supplied by Schemathesis, not by a pytest fixture. `client` is the
# normal pytest fixture that provides the running in-process FastAPI app.
@schema.parametrize()
def test_generated_read_only_responses_conform_to_openapi(
    case: Any,
    client: TestClient,
) -> None:
    """Generated safe requests receive responses valid for their OpenAPI schema."""
    # TestClient sends the generated request directly to the running ASGI app.
    # Schemathesis then checks the status code, headers, and response body
    # against the operation described in `/openapi.json`.
    case.call_and_validate(session=client)


# HELPERS


def assert_schema_fields(schema: dict[str, Any], expected_fields: set[str]) -> None:
    """Confirm a component is an object with the expected documented fields."""
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == expected_fields
    assert set(schema["required"]) == expected_fields - {"completed"}


def paths_response_schema(
    openapi_document: dict[str, Any],
    path: str,
    method: str,
    status_code: str,
) -> dict[str, str]:
    """Return one operation's JSON response schema from the OpenAPI document."""
    return openapi_document["paths"][path][method]["responses"][status_code][
        "content"
    ]["application/json"]["schema"]


def create_project(client: TestClient) -> dict[str, Any]:
    """Create a parent Project required by the conflict scenario."""
    response = client.post(
        "/projects",
        json={"name": "Conflict Project", "description": "Has a related Task."},
    )
    assert response.status_code == 201
    return response.json()


def create_task(client: TestClient, project_id: int) -> dict[str, Any]:
    """Create the Task that makes Project deletion a conflict."""
    response = client.post(
        "/tasks",
        json={
            "title": "Related Task",
            "description": "Creates the delete conflict.",
            "completed": False,
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    return response.json()
