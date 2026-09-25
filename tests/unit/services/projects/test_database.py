"""Unit tests for DatabaseProjectService with mocked repositories."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import ProjectNotFoundError
from app.models.project import Project
from app.schemas.projects import ProjectInput
from app.services.projects import DatabaseProjectService


@pytest.fixture
def session_factory() -> tuple[MagicMock, MagicMock, MagicMock]:
    session = MagicMock()
    factory = MagicMock()

    @contextmanager
    def session_context():
        yield session

    @contextmanager
    def transaction_context():
        yield session

    factory.side_effect = session_context
    factory.begin.side_effect = transaction_context
    return factory, session, MagicMock()


def test_create_project_uses_repository_and_transaction(
    session_factory: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    factory, session, repository = session_factory
    project = Project(id=1, name="Course API", description="Demo")
    repository.create.return_value = project

    with patch(
        "app.services.projects.database.ProjectRepository",
        return_value=repository,
    ):
        result = DatabaseProjectService(factory).create_project(
            ProjectInput(name="Course API", description="Demo")
        )

    assert result is project
    repository.create.assert_called_once()
    session.refresh.assert_called_once_with(project)
    factory.begin.assert_called_once_with()


def test_get_project_translates_missing_repository_result(
    session_factory: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    factory, _, repository = session_factory
    repository.get_by_id.return_value = None

    with patch(
        "app.services.projects.database.ProjectRepository",
        return_value=repository,
    ):
        with pytest.raises(ProjectNotFoundError):
            DatabaseProjectService(factory).get_project(999)
