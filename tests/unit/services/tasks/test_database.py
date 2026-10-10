"""Unit tests for DatabaseTaskService with mocked repositories."""

from collections.abc import Generator

import pytest
from mockito import args, mock, unstub, verify, when

import app.services.tasks.database as database_module
from app.exceptions import ProjectNotFoundError
from app.schemas.tasks import TaskInput
from app.services.tasks import DatabaseTaskService


@pytest.fixture
def session_factory() -> Generator[
    tuple[object, object, object, object], None, None
]:
    """Build fake sessions and repositories for service unit tests.

    ``session_factory.begin()`` is used inside a ``with`` statement by the
    production service. Mockito therefore needs ``__enter__`` to yield the
    fake Session and ``__exit__`` to complete the context-manager protocol.
    ``unstub`` removes these stubs after each test.
    """
    session = mock()
    factory = mock()
    project_repository = mock()
    task_repository = mock()
    transaction_context = mock()

    # Simulate: ``with session_factory.begin() as session``.
    when(transaction_context).__enter__().thenReturn(session)
    # `__exit__` receives exception details; `args` matches any such values.
    when(transaction_context).__exit__(*args)
    when(factory).begin().thenReturn(transaction_context)
    try:
        # Yield the fake collaborators to the test. Pytest pauses this fixture
        # here while the test runs.
        yield factory, session, project_repository, task_repository
    finally:
        # Remove Mockito stubs so they cannot affect a later test.
        unstub()


def test_create_task_checks_parent_and_uses_task_repository(
    session_factory: tuple[object, object, object, object],
) -> None:
    factory, session, project_repository, task_repository = session_factory
    when(project_repository).get_by_id(1).thenReturn(object())
    task = mock()
    when(task_repository).create(...).thenReturn(task)

    with (
        when(database_module).ProjectRepository(session).thenReturn(
            project_repository
        ),
        when(database_module).TaskRepository(session).thenReturn(task_repository),
    ):
        result = DatabaseTaskService(factory).create_task(
            TaskInput(title="Write tests", description="Test service", project_id=1)
        )

    assert result is task
    verify(project_repository, times=1).get_by_id(1)
    verify(task_repository, times=1).create(...)
    verify(session, times=1).refresh(task)


def test_create_task_rejects_missing_parent_without_creating_task(
    session_factory: tuple[object, object, object, object],
) -> None:
    factory, session, project_repository, task_repository = session_factory
    when(project_repository).get_by_id(999).thenReturn(None)

    with (
        when(database_module).ProjectRepository(session).thenReturn(
            project_repository
        ),
    ):
        with pytest.raises(ProjectNotFoundError):
            DatabaseTaskService(factory).create_task(
                TaskInput(
                    title="Orphan task",
                    description="Invalid parent",
                    project_id=999,
                )
            )

    verify(task_repository, times=0).create(...)
