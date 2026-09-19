"""Abstract Project service contract."""

from abc import ABC, abstractmethod

from app.models.project import Project
from app.models.task import Task
from app.schemas.projects import ProjectInput


class ProjectService(ABC):
    """Define Project use-case operations shared by all implementations."""

    @abstractmethod
    def list_projects(self) -> list[Project]:
        """Return every Project."""

    @abstractmethod
    def get_project(self, project_id: int) -> Project:
        """Return one Project or raise ProjectNotFoundError."""

    @abstractmethod
    def create_project(self, data: ProjectInput) -> Project:
        """Create and return a Project."""

    @abstractmethod
    def replace_project(self, project_id: int, data: ProjectInput) -> Project:
        """Replace and return one Project."""

    @abstractmethod
    def delete_project(self, project_id: int) -> None:
        """Delete a Project when its business rules allow it."""

    @abstractmethod
    def list_project_tasks(self, project_id: int) -> list[Task]:
        """Return the Tasks associated with one Project."""
