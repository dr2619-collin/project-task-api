"""In-memory Task service implementation."""

from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.task import Task
from app.schemas.tasks import TaskInput
from app.services.in_memory_store import InMemoryStore
from .base import TaskService


class InMemoryTaskService(TaskService):
    """Implement Task use cases with shared in-memory state.

    Data is process-local and non-durable.
    """

    def __init__(self, store: InMemoryStore):
        self._store = store

    def list_tasks(self) -> list[Task]:
        with self._store.lock:
            return list(self._store.tasks)

    def get_task(self, task_id: int) -> Task:
        with self._store.lock:
            for task in self._store.tasks:
                if task.id == task_id:
                    return task
            raise TaskNotFoundError

    def create_task(self, data: TaskInput) -> Task:
        # Validate, generate the ID, and append while holding the lock.
        with self._store.lock:
            if not any(
                project.id == data.project_id for project in self._store.projects
            ):
                raise ProjectNotFoundError
            task = Task(
                id=max((item.id for item in self._store.tasks), default=0) + 1,
                **data.model_dump(),
            )
            self._store.tasks.append(task)
            return task

    def replace_task(self, task_id: int, data: TaskInput) -> Task:
        with self._store.lock:
            task = self.get_task(task_id)
            if not any(
                project.id == data.project_id for project in self._store.projects
            ):
                raise ProjectNotFoundError
            task.title = data.title
            task.description = data.description
            task.completed = data.completed
            task.project_id = data.project_id
            return task

    def delete_task(self, task_id: int) -> None:
        with self._store.lock:
            self._store.tasks.remove(self.get_task(task_id))
