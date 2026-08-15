"""Unit tests for every public ProjectService operation."""

from unittest.mock import MagicMock

import pytest

from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.schemas.projects import ProjectCreate, ProjectUpdate
from app.services.projects import ProjectService


@pytest.fixture
def project_service() -> tuple[ProjectService, MagicMock]:
    """Create a service with mocked collaborators instead of a real database."""
    session = MagicMock()
    service = ProjectService(session)
    service.project_repository = MagicMock()
    service.task_repository = MagicMock()
    return service, session


@pytest.fixture
def project() -> Project:
    """Provide one Project for service scenarios that need an existing record."""
    return Project(id=1, name="Course API", description="Course demonstration")


@pytest.fixture
def project_create_data() -> ProjectCreate:
    """Provide valid data for a new Project."""
    return ProjectCreate(name="Testing Module", description="Add service tests.")


@pytest.fixture
def project_update_data() -> ProjectUpdate:
    """Provide valid replacement data for a Project."""
    return ProjectUpdate(name="Updated Module", description="Replace service data.")


def test_list_projects_returns_repository_result(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
) -> None:
    """Listing Projects delegates retrieval and returns the resulting records."""
    service, _ = project_service
    service.project_repository.list_all.return_value = [project]

    result = service.list_projects()

    assert result == [project]
    service.project_repository.list_all.assert_called_once_with()


def test_get_project_returns_existing_project(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
) -> None:
    """An existing Project is returned to the caller."""
    service, _ = project_service
    service.project_repository.get_by_id.return_value = project

    assert service.get_project(project.id) is project
    service.project_repository.get_by_id.assert_called_once_with(project.id)


def test_get_project_rejects_missing_project(
    project_service: tuple[ProjectService, MagicMock],
) -> None:
    """A missing Project is expressed as a service-layer exception."""
    service, _ = project_service
    service.project_repository.get_by_id.return_value = None

    with pytest.raises(ProjectNotFoundError):
        service.get_project(999)


def test_create_project_commits_and_refreshes_new_project(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
    project_create_data: ProjectCreate,
) -> None:
    """Creating a Project commits the transaction and refreshes the ORM object."""
    service, session = project_service
    service.project_repository.create.return_value = project

    result = service.create_project(project_create_data)

    assert result is project
    service.project_repository.create.assert_called_once_with(project_create_data)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(project)


def test_create_project_rolls_back_when_repository_fails(
    project_service: tuple[ProjectService, MagicMock],
    project_create_data: ProjectCreate,
) -> None:
    """A failed Project creation rolls back its transaction."""
    service, session = project_service
    service.project_repository.create.side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        service.create_project(project_create_data)

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_replace_project_commits_and_refreshes_updated_project(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
    project_update_data: ProjectUpdate,
) -> None:
    """Replacing an existing Project commits and returns the updated object."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = project
    service.project_repository.replace.return_value = project

    result = service.replace_project(project.id, project_update_data)

    assert result is project
    service.project_repository.replace.assert_called_once_with(project, project_update_data)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(project)


def test_replace_project_rejects_missing_project(
    project_service: tuple[ProjectService, MagicMock],
    project_update_data: ProjectUpdate,
) -> None:
    """Replacing a missing Project does not attempt a database update."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = None

    with pytest.raises(ProjectNotFoundError):
        service.replace_project(999, project_update_data)

    service.project_repository.replace.assert_not_called()
    session.commit.assert_not_called()


def test_replace_project_rolls_back_when_repository_fails(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
    project_update_data: ProjectUpdate,
) -> None:
    """A failed Project replacement rolls back its transaction."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = project
    service.project_repository.replace.side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        service.replace_project(project.id, project_update_data)

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_delete_project_commits_when_project_has_no_tasks(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
) -> None:
    """A Project without related Tasks is deleted and committed."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = project
    service.task_repository.exists_for_project.return_value = False

    service.delete_project(project.id)

    service.project_repository.delete.assert_called_once_with(project)
    session.commit.assert_called_once_with()


def test_delete_project_rejects_project_with_tasks(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
) -> None:
    """A Project with related Tasks must not be deleted."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = project
    service.task_repository.exists_for_project.return_value = True

    with pytest.raises(ProjectHasTasksError):
        service.delete_project(project.id)

    service.project_repository.delete.assert_not_called()
    session.commit.assert_not_called()


def test_delete_project_rejects_missing_project(
    project_service: tuple[ProjectService, MagicMock],
) -> None:
    """Deleting a missing Project never checks Tasks or commits."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = None

    with pytest.raises(ProjectNotFoundError):
        service.delete_project(999)

    service.task_repository.exists_for_project.assert_not_called()
    session.commit.assert_not_called()


def test_delete_project_rolls_back_when_repository_fails(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
) -> None:
    """A failed Project deletion rolls back its transaction."""
    service, session = project_service
    service.project_repository.get_by_id.return_value = project
    service.task_repository.exists_for_project.return_value = False
    service.project_repository.delete.side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        service.delete_project(project.id)

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_list_project_tasks_returns_tasks_for_existing_project(
    project_service: tuple[ProjectService, MagicMock],
    project: Project,
) -> None:
    """Listing a Project's Tasks first verifies that the Project exists."""
    service, _ = project_service
    task = Task(
        id=1,
        title="Write tests",
        description="Add ProjectService tests.",
        completed=False,
        project_id=project.id,
    )
    service.project_repository.get_by_id.return_value = project
    service.task_repository.list_by_project.return_value = [task]

    result = service.list_project_tasks(project.id)

    assert result == [task]
    service.task_repository.list_by_project.assert_called_once_with(project.id)


def test_list_project_tasks_rejects_missing_project(
    project_service: tuple[ProjectService, MagicMock],
) -> None:
    """A missing Project cannot have its related Tasks listed."""
    service, _ = project_service
    service.project_repository.get_by_id.return_value = None

    with pytest.raises(ProjectNotFoundError):
        service.list_project_tasks(999)

    service.task_repository.list_by_project.assert_not_called()
