"""Business operations for Projects."""

from sqlalchemy.orm import Session

from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectService:
    """Coordinate Project rules, repositories, and transactions."""

    def __init__(self, session: Session):
        self.session = session
        self.project_repository = ProjectRepository(session)
        self.task_repository = TaskRepository(session)

    def list_projects(self) -> list[Project]:
        return self.project_repository.list_all()

    def get_project(self, project_id: int) -> Project:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError
        return project

    def create_project(self, data: ProjectCreate) -> Project:
        try:
            project = self.project_repository.create(data)
            self.session.commit()
            self.session.refresh(project)
            return project
        except Exception:
            self.session.rollback()
            raise

    def replace_project(self, project_id: int, data: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        try:
            updated_project = self.project_repository.replace(project, data)
            self.session.commit()
            self.session.refresh(updated_project)
            return updated_project
        except Exception:
            self.session.rollback()
            raise

    def delete_project(self, project_id: int) -> None:
        project = self.get_project(project_id)
        if self.task_repository.exists_for_project(project_id):
            raise ProjectHasTasksError
        try:
            self.project_repository.delete(project)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def list_project_tasks(self, project_id: int) -> list[Task]:
        self.get_project(project_id)
        return self.task_repository.list_by_project(project_id)
