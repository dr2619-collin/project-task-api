"""Application-level Task service contract."""

from abc import ABC, abstractmethod

from app.models.task import Task
from app.schemas.tasks import TaskInput


class TaskService(ABC):
    """Define Task use-case operations shared by all implementations."""

    @abstractmethod
    def list_tasks(self) -> list[Task]:
        """Return every Task."""

    @abstractmethod
    def get_task(self, task_id: int) -> Task:
        """Return one Task or raise TaskNotFoundError."""

    @abstractmethod
    def create_task(self, data: TaskInput) -> Task:
        """Create and return a Task."""

    @abstractmethod
    def replace_task(self, task_id: int, data: TaskInput) -> Task:
        """Replace and return one Task."""

    @abstractmethod
    def delete_task(self, task_id: int) -> None:
        """Delete a Task."""
