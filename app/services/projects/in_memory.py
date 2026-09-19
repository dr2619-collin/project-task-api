"""In-memory Project service implementation."""

from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.schemas.projects import ProjectInput
from app.services.in_memory_store import InMemoryStore
from .base import ProjectService


class InMemoryProjectService(ProjectService):
    """Implement Project use cases with shared in-memory state.

    Data is process-local and non-durable.
    """

    def __init__(self, store: InMemoryStore):
        self._store = store

    def list_projects(self) -> list[Project]:
        with self._store.lock:
            return list(self._store.projects)

    def get_project(self, project_id: int) -> Project:
        with self._store.lock:
            for project in self._store.projects:
                if project.id == project_id:
                    return project
            raise ProjectNotFoundError

    def create_project(self, data: ProjectInput) -> Project:
        # Lock ID generation and append as one operation.
        with self._store.lock:
            project = Project(
                id=max((item.id for item in self._store.projects), default=0) + 1,
                **data.model_dump(),
            )
            self._store.projects.append(project)
            return project

    def replace_project(self, project_id: int, data: ProjectInput) -> Project:
        with self._store.lock:
            project = self.get_project(project_id)
            project.name = data.name
            project.description = data.description
            return project

    def delete_project(self, project_id: int) -> None:
        with self._store.lock:
            project = self.get_project(project_id)
            if any(task.project_id == project_id for task in self._store.tasks):
                raise ProjectHasTasksError
            self._store.projects.remove(project)

    def list_project_tasks(self, project_id: int) -> list[Task]:
        with self._store.lock:
            self.get_project(project_id)
            return [
                task for task in self._store.tasks if task.project_id == project_id
            ]
