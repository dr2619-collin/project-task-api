"""Import ORM models so SQLAlchemy discovers every mapped table."""

from app.models.project import Project
from app.models.task import Task

__all__ = ["Project", "Task"]
