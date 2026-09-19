"""Relational-database Project service implementation."""

from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.projects import ProjectInput
from .base import ProjectService


class DatabaseProjectService(ProjectService):
    """Implement Project use cases with database persistence.

    The service applies application rules and defines transaction boundaries.
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        # Share the factory; each operation creates its own Session.
        self._session_factory = session_factory

    def list_projects(self) -> list[Project]:
        with self._session_factory() as session:
            return ProjectRepository(session).list_all()

    def get_project(self, project_id: int) -> Project:
        with self._session_factory() as session:
            project = ProjectRepository(session).get_by_id(project_id)
            if project is None:
                raise ProjectNotFoundError
            return project

    def create_project(self, data: ProjectInput) -> Project:
        # begin() commits on success and rolls back if an exception escapes.
        with self._session_factory.begin() as session:
            project = ProjectRepository(session).create(data)
            session.refresh(project)
            return project

    def replace_project(self, project_id: int, data: ProjectInput) -> Project:
        # Read, validate, update, and commit are one atomic use case.
        with self._session_factory.begin() as session:
            repository = ProjectRepository(session)
            project = repository.get_by_id(project_id)
            if project is None:
                raise ProjectNotFoundError
            updated_project = repository.replace(project, data)
            session.refresh(updated_project)
            return updated_project

    def delete_project(self, project_id: int) -> None:
        # Check and delete belong to one transaction.
        with self._session_factory.begin() as session:
            repository = ProjectRepository(session)
            project = repository.get_by_id(project_id)
            if project is None:
                raise ProjectNotFoundError
            if TaskRepository(session).exists_for_project(project_id):
                raise ProjectHasTasksError
            repository.delete(project)

    def list_project_tasks(self, project_id: int) -> list[Task]:
        with self._session_factory() as session:
            if ProjectRepository(session).get_by_id(project_id) is None:
                raise ProjectNotFoundError
            return TaskRepository(session).list_by_project(project_id)
