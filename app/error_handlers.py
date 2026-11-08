"""Centralized conversion of application failures into RFC 9457 responses."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import DomainError

# Shared base for the problem type URIs returned by this API.
PROBLEM_BASE_URL = "https://project-task-api.local/problems/"


def problem_response(
    request: Request,
    *,
    problem_type: str,
    title: str,
    status_code: int,
    detail: str,
    errors: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Create one consistent application/problem+json response."""
    # Keep the public error shape consistent, regardless of where the error began.
    body: dict[str, Any] = {
        "type": f"{PROBLEM_BASE_URL}{problem_type}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body),
        media_type="application/problem+json",
        headers=headers,
    )


def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """Expose a service-layer business failure without router-specific handling."""
    return problem_response(
        request,
        problem_type=exc.problem_type,
        title=exc.title,
        status_code=exc.status_code,
        detail=exc.detail,
    )


def handle_http_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Convert authentication, authorization, and framework HTTP errors."""
    # Give common HTTP failures stable problem names; retain a generic fallback
    # for other HTTP statuses, such as Method Not Allowed (405).
    known_problems = {
        status.HTTP_401_UNAUTHORIZED: ("unauthorized", "Unauthorized"),
        status.HTTP_403_FORBIDDEN: ("forbidden", "Forbidden"),
        status.HTTP_404_NOT_FOUND: ("not-found", "Not found"),
        status.HTTP_409_CONFLICT: ("conflict", "Conflict"),
    }
    problem_type, title = known_problems.get(
        exc.status_code, ("http-error", "HTTP error")
    )
    detail = (
        exc.detail
        if isinstance(exc.detail, str)
        else "The request could not be completed."
    )
    return problem_response(
        request,
        problem_type=problem_type,
        title=title,
        status_code=exc.status_code,
        detail=detail,
        headers=exc.headers,
    )


def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return FastAPI/Pydantic validation details in a stable error envelope."""
    # Include field-level validation issues while keeping the overall format shared.
    return problem_response(
        request,
        problem_type="validation-error",
        title="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="One or more request values are invalid.",
        errors=exc.errors(),
    )


def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
    """Return a safe response without exposing unexpected failure details."""
    # Do not send exception internals to clients; unexpected errors become safe 500s.
    return problem_response(
        request,
        problem_type="internal-server-error",
        title="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="The server encountered an unexpected condition.",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register the shared HTTP representation policy on the application."""
    # Register specific exception families before the catch-all Exception handler.
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_error)
