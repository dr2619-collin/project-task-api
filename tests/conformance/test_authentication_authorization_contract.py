"""Conformance tests for the documented Module 08 security contract."""

from typing import Any

import pytest
from starlette.testclient import TestClient


# OPENAPI SECURITY SCHEME
# HTTPBearer adds the reusable scheme to OpenAPI. The protected route
# dependencies add a security requirement to each resource operation.


def test_openapi_declares_the_bearer_authentication_scheme(client: TestClient) -> None:
    """API clients can discover the Bearer scheme from the public contract."""
    document = client.get("/openapi.json").json()
    scheme = document["components"]["securitySchemes"]["BearerAuthentication"]

    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"


@pytest.mark.parametrize(
    ("path", "method", "expected_statuses"),
    [
        ("/projects", "get", {"200", "401"}),
        ("/projects", "post", {"201", "401", "403", "422"}),
        ("/projects/{project_id}", "put", {"200", "401", "403", "404", "422"}),
        ("/tasks", "get", {"200", "401"}),
        ("/tasks", "post", {"201", "401", "403", "404", "422"}),
        ("/tasks/{task_id}", "delete", {"204", "401", "403", "404", "422"}),
    ],
)
def test_openapi_marks_resource_operations_as_bearer_protected(
    client: TestClient,
    path: str,
    method: str,
    expected_statuses: set[str],
) -> None:
    """Representative operations publish Bearer security and expected outcomes."""
    operation = client.get("/openapi.json").json()["paths"][path][method]

    assert operation["security"] == [{"BearerAuthentication": []}]
    assert expected_statuses <= set(operation["responses"])
