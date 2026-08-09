"""Database operations for Task records."""

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate


class TaskRepository:
    """Read and write Task rows through one SQLAlchemy session."""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Task]:
        statement = select(Task).order_by(Task.id)
        return list(self.session.scalars(statement))

    def list_by_project(self, project_id: int) -> list[Task]:
        statement = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.id)
        )
        return list(self.session.scalars(statement))

    def get_by_id(self, task_id: int) -> Task | None:
        return self.session.get(Task, task_id)

    def exists_for_project(self, project_id: int) -> bool:
        statement = select(exists().where(Task.project_id == project_id))
        return bool(self.session.scalar(statement))

    def create(self, data: TaskCreate) -> Task:
        task = Task(**data.model_dump())
        self.session.add(task)
        self.session.flush()
        return task

    def replace(self, task: Task, data: TaskUpdate) -> Task:
        for field, value in data.model_dump().items():
            setattr(task, field, value)
        self.session.flush()
        return task

    def delete(self, task: Task) -> None:
        self.session.delete(task)
