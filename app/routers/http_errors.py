"""Translate application outcomes into HTTP responses for API routes."""

from fastapi import HTTPException, status


def project_not_found() -> HTTPException:
    """Return the HTTP 404 response for a missing Project.

    This mapping belongs in the router package because HTTPException is a
    FastAPI transport concern, not a business-rule concern.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )


def task_not_found() -> HTTPException:
    """Return the HTTP 404 response for a missing Task."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Task not found",
    )


def project_has_tasks() -> HTTPException:
    """Return the HTTP 409 response for a Project with related Tasks."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Delete the project's tasks before deleting the project",
    )
