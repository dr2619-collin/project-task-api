"""FastAPI dependencies that expose application services to HTTP routes."""

from fastapi import Request

from app.config import Settings
from app.services.projects import ProjectService
from app.services.tasks import TaskService


def get_settings(request: Request) -> Settings:
    """Return the validated settings created during application startup."""
    return request.app.state.settings


def get_project_service(request: Request) -> ProjectService:
    """Return the startup-selected Project service."""
    return request.app.state.project_service


def get_task_service(request: Request) -> TaskService:
    """Return the startup-selected Task service."""
    return request.app.state.task_service
