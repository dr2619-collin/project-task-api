"""Business operations for Tasks."""

from sqlalchemy.orm import Session

from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.task import Task
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.tasks import TaskCreate, TaskUpdate


class TaskService:
    """Coordinate Task rules, repositories, and transactions."""

    def __init__(self, session: Session):
        self.session = session
        self.projects = ProjectRepository(session)
        self.tasks = TaskRepository(session)

    def _require_project(self, project_id: int) -> None:
        if self.projects.get_by_id(project_id) is None:
            raise ProjectNotFoundError

    def list_tasks(self) -> list[Task]:
        return self.tasks.list_all()

    def get_task(self, task_id: int) -> Task:
        task = self.tasks.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError
        return task

    def create_task(self, data: TaskCreate) -> Task:
        self._require_project(data.project_id)
        try:
            task = self.tasks.create(data)
            self.session.commit()
            self.session.refresh(task)
            return task
        except Exception:
            self.session.rollback()
            raise

    def replace_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = self.get_task(task_id)
        self._require_project(data.project_id)
        try:
            updated_task = self.tasks.replace(task, data)
            self.session.commit()
            self.session.refresh(updated_task)
            return updated_task
        except Exception:
            self.session.rollback()
            raise

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        try:
            self.tasks.delete(task)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
