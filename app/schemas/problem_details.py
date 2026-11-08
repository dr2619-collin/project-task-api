"""Shared RFC 9457 Problem Details schema and OpenAPI response metadata."""

from typing import Any

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """Describe a client-visible API error using RFC 9457 fields."""

    type: str = Field(description="Stable URI identifying the kind of problem.")
    title: str = Field(description="Short, human-readable summary of the problem.")
    status: int = Field(description="HTTP status code for this occurrence.")
    detail: str = Field(description="Human-readable explanation for this occurrence.")
    instance: str = Field(description="Request path where this problem occurred.")
    errors: list[dict[str, Any]] | None = Field(
        default=None,
        description="Validation details when the client request cannot be accepted.",
    )


def problem_response(
    description: str,
    *,
    headers: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build OpenAPI metadata for an RFC 9457 Problem Details response."""
    response: dict[str, Any] = {
        "description": description,
        "content": {
            "application/problem+json": {
                "schema": ProblemDetails.model_json_schema(),
            }
        },
    }
    if headers is not None:
        response["headers"] = headers
    return response


UNAUTHORIZED_PROBLEM_RESPONSE = problem_response(
    "Missing or invalid Bearer token.",
    headers={
        "WWW-Authenticate": {
            "description": "Authentication scheme required by this endpoint.",
            "schema": {"type": "string"},
        }
    },
)
FORBIDDEN_PROBLEM_RESPONSE = problem_response("Administrator role required.")
PROJECT_NOT_FOUND_RESPONSE = problem_response("Project not found.")
TASK_NOT_FOUND_RESPONSE = problem_response("Task not found.")
RELATED_RESOURCE_NOT_FOUND_RESPONSE = problem_response(
    "Task or related Project not found."
)
CONFLICT_PROBLEM_RESPONSE = problem_response(
    "The requested operation conflicts with current state."
)
VALIDATION_PROBLEM_RESPONSE = problem_response(
    "One or more request values are invalid."
)
