"""Unit tests for every public TaskService operation."""

from unittest.mock import MagicMock

import pytest

from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate
from app.services.tasks import TaskService


@pytest.fixture
def task_service() -> tuple[TaskService, MagicMock]:
    """Create a Task service with mocked database collaborators."""
    session = MagicMock()
    service = TaskService(session)
    service.project_repository = MagicMock()
    service.task_repository = MagicMock()
    return service, session


@pytest.fixture
def project() -> Project:
    """Provide an existing Project for Task relationship checks."""
    return Project(id=1, name="Course API", description="Course demonstration")


@pytest.fixture
def task() -> Task:
    """Provide an existing Task for retrieval, replacement, and deletion."""
    return Task(
        id=1,
        title="Write tests",
        description="Add TaskService tests.",
        completed=False,
        project_id=1,
    )


@pytest.fixture
def task_create_data() -> TaskCreate:
    """Provide valid data for a new Task."""
    return TaskCreate(
        title="Write tests",
        description="Add TaskService tests.",
        project_id=1,
    )


@pytest.fixture
def task_update_data() -> TaskUpdate:
    """Provide valid replacement data for a Task."""
    return TaskUpdate(
        title="Update tests",
        description="Replace TaskService data.",
        completed=True,
        project_id=1,
    )


def test_list_tasks_returns_repository_result(
    task_service: tuple[TaskService, MagicMock],
    task: Task,
) -> None:
    """Listing Tasks delegates retrieval and returns the resulting records."""
    service, _ = task_service
    service.task_repository.list_all.return_value = [task]

    result = service.list_tasks()

    assert result == [task]
    service.task_repository.list_all.assert_called_once_with()


def test_get_task_returns_existing_task(
    task_service: tuple[TaskService, MagicMock],
    task: Task,
) -> None:
    """An existing Task is returned to the caller."""
    service, _ = task_service
    service.task_repository.get_by_id.return_value = task

    assert service.get_task(task.id) is task
    service.task_repository.get_by_id.assert_called_once_with(task.id)


def test_get_task_rejects_missing_task(
    task_service: tuple[TaskService, MagicMock],
) -> None:
    """A missing Task is expressed as a service-layer exception."""
    service, _ = task_service
    service.task_repository.get_by_id.return_value = None

    with pytest.raises(TaskNotFoundError):
        service.get_task(999)


def test_create_task_commits_and_refreshes_new_task(
    task_service: tuple[TaskService, MagicMock],
    project: Project,
    task: Task,
    task_create_data: TaskCreate,
) -> None:
    """Creating a Task verifies its Project, commits, and refreshes the Task."""
    service, session = task_service
    service.project_repository.get_by_id.return_value = project
    service.task_repository.create.return_value = task

    result = service.create_task(task_create_data)

    assert result is task
    service.task_repository.create.assert_called_once_with(task_create_data)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(task)


def test_create_task_rejects_nonexistent_project(
    task_service: tuple[TaskService, MagicMock],
    task_create_data: TaskCreate,
) -> None:
    """A Task cannot be created for a Project that does not exist."""
    service, session = task_service
    service.project_repository.get_by_id.return_value = None

    with pytest.raises(ProjectNotFoundError):
        service.create_task(task_create_data)

    service.task_repository.create.assert_not_called()
    session.commit.assert_not_called()


def test_create_task_rolls_back_when_repository_fails(
    task_service: tuple[TaskService, MagicMock],
    project: Project,
    task_create_data: TaskCreate,
) -> None:
    """A failed Task creation rolls back its transaction."""
    service, session = task_service
    service.project_repository.get_by_id.return_value = project
    service.task_repository.create.side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        service.create_task(task_create_data)

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_replace_task_commits_and_refreshes_updated_task(
    task_service: tuple[TaskService, MagicMock],
    project: Project,
    task: Task,
    task_update_data: TaskUpdate,
) -> None:
    """Replacing a Task verifies both Task and Project before committing."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = task
    service.project_repository.get_by_id.return_value = project
    service.task_repository.replace.return_value = task

    result = service.replace_task(task.id, task_update_data)

    assert result is task
    service.task_repository.replace.assert_called_once_with(task, task_update_data)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(task)


def test_replace_task_rejects_missing_task(
    task_service: tuple[TaskService, MagicMock],
    task_update_data: TaskUpdate,
) -> None:
    """Replacing a missing Task does not check its requested Project."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = None

    with pytest.raises(TaskNotFoundError):
        service.replace_task(999, task_update_data)

    service.project_repository.get_by_id.assert_not_called()
    session.commit.assert_not_called()


def test_replace_task_rejects_nonexistent_project(
    task_service: tuple[TaskService, MagicMock],
    task: Task,
    task_update_data: TaskUpdate,
) -> None:
    """Replacing a Task rejects a replacement Project that does not exist."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = task
    service.project_repository.get_by_id.return_value = None

    with pytest.raises(ProjectNotFoundError):
        service.replace_task(task.id, task_update_data)

    service.task_repository.replace.assert_not_called()
    session.commit.assert_not_called()


def test_replace_task_rolls_back_when_repository_fails(
    task_service: tuple[TaskService, MagicMock],
    project: Project,
    task: Task,
    task_update_data: TaskUpdate,
) -> None:
    """A failed Task replacement rolls back its transaction."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = task
    service.project_repository.get_by_id.return_value = project
    service.task_repository.replace.side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        service.replace_task(task.id, task_update_data)

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_delete_task_commits_when_task_exists(
    task_service: tuple[TaskService, MagicMock],
    task: Task,
) -> None:
    """Deleting an existing Task removes it and commits the transaction."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = task

    service.delete_task(task.id)

    service.task_repository.delete.assert_called_once_with(task)
    session.commit.assert_called_once_with()


def test_delete_task_rejects_missing_task(
    task_service: tuple[TaskService, MagicMock],
) -> None:
    """Deleting a missing Task does not attempt a database mutation."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = None

    with pytest.raises(TaskNotFoundError):
        service.delete_task(999)

    service.task_repository.delete.assert_not_called()
    session.commit.assert_not_called()


def test_delete_task_rolls_back_when_repository_fails(
    task_service: tuple[TaskService, MagicMock],
    task: Task,
) -> None:
    """A failed Task deletion rolls back its transaction."""
    service, session = task_service
    service.task_repository.get_by_id.return_value = task
    service.task_repository.delete.side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        service.delete_task(task.id)

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
