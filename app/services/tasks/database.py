"""Relational-database Task service implementation."""

from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.task import Task
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.tasks import TaskInput
from .base import TaskService


class DatabaseTaskService(TaskService):
    """Implement Task use cases with database persistence.

    The service applies application rules and defines transaction boundaries.
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        # Share the factory; each operation creates its own Session.
        self._session_factory = session_factory

    def list_tasks(self) -> list[Task]:
        with self._session_factory() as session:
            return TaskRepository(session).list_all()

    def get_task(self, task_id: int) -> Task:
        with self._session_factory() as session:
            task = TaskRepository(session).get_by_id(task_id)
            if task is None:
                raise TaskNotFoundError
            return task

    def create_task(self, data: TaskInput) -> Task:
        # Verify the parent and insert the child atomically.
        with self._session_factory.begin() as session:
            if ProjectRepository(session).get_by_id(data.project_id) is None:
                raise ProjectNotFoundError
            task = TaskRepository(session).create(data)
            session.refresh(task)
            return task

    def replace_task(self, task_id: int, data: TaskInput) -> Task:
        # Lookup, validation, update, and commit are one atomic use case.
        with self._session_factory.begin() as session:
            task_repository = TaskRepository(session)
            task = task_repository.get_by_id(task_id)
            if task is None:
                raise TaskNotFoundError
            if ProjectRepository(session).get_by_id(data.project_id) is None:
                raise ProjectNotFoundError
            updated_task = task_repository.replace(task, data)
            session.refresh(updated_task)
            return updated_task

    def delete_task(self, task_id: int) -> None:
        with self._session_factory.begin() as session:
            task_repository = TaskRepository(session)
            task = task_repository.get_by_id(task_id)
            if task is None:
                raise TaskNotFoundError
            task_repository.delete(task)
