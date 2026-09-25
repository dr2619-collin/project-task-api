"""Unit tests for DatabaseTaskService with mocked repositories."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import ProjectNotFoundError
from app.schemas.tasks import TaskInput
from app.services.tasks import DatabaseTaskService


@pytest.fixture
def session_factory() -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    session = MagicMock()
    factory = MagicMock()
    project_repository = MagicMock()
    task_repository = MagicMock()

    @contextmanager
    def transaction_context():
        yield session

    factory.begin.side_effect = transaction_context
    return factory, session, project_repository, task_repository


def test_create_task_checks_parent_and_uses_task_repository(
    session_factory: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    factory, session, project_repository, task_repository = session_factory
    project_repository.get_by_id.return_value = object()
    task = MagicMock()
    task_repository.create.return_value = task

    with (
        patch(
            "app.services.tasks.database.ProjectRepository",
            return_value=project_repository,
        ),
        patch(
            "app.services.tasks.database.TaskRepository",
            return_value=task_repository,
        ),
    ):
        result = DatabaseTaskService(factory).create_task(
            TaskInput(title="Write tests", description="Test service", project_id=1)
        )

    assert result is task
    project_repository.get_by_id.assert_called_once_with(1)
    task_repository.create.assert_called_once()
    session.refresh.assert_called_once_with(task)


def test_create_task_rejects_missing_parent_without_creating_task(
    session_factory: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    factory, _, project_repository, task_repository = session_factory
    project_repository.get_by_id.return_value = None

    with patch(
        "app.services.tasks.database.ProjectRepository",
        return_value=project_repository,
    ), patch(
        "app.services.tasks.database.TaskRepository",
        return_value=task_repository,
    ):
        with pytest.raises(ProjectNotFoundError):
            DatabaseTaskService(factory).create_task(
                TaskInput(
                    title="Orphan task",
                    description="Invalid parent",
                    project_id=999,
                )
            )

    task_repository.create.assert_not_called()
