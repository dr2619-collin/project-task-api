"""Unit tests for the in-memory Task service contract."""

import pytest

from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.project import Project
from app.schemas.tasks import TaskInput
from app.services.in_memory_store import InMemoryStore
from app.services.tasks import InMemoryTaskService


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def service(store: InMemoryStore) -> InMemoryTaskService:
    return InMemoryTaskService(store)


def add_project(store: InMemoryStore) -> Project:
    project = Project(id=1, name="Course API", description="Course demonstration")
    store.projects.append(project)
    return project


def task_data(title: str = "Write tests") -> TaskInput:
    return TaskInput(
        title=title,
        description="Add service tests",
        project_id=1,
    )


def test_create_task_requires_existing_project(
    service: InMemoryTaskService,
) -> None:
    with pytest.raises(ProjectNotFoundError):
        service.create_task(task_data())


def test_create_list_and_get_task(
    store: InMemoryStore, service: InMemoryTaskService
) -> None:
    add_project(store)

    created = service.create_task(task_data())

    assert created.id == 1
    assert service.list_tasks() == [created]
    assert service.get_task(created.id) is created


def test_get_task_raises_for_missing_id(service: InMemoryTaskService) -> None:
    with pytest.raises(TaskNotFoundError):
        service.get_task(999)


def test_replace_task_updates_fields(
    store: InMemoryStore, service: InMemoryTaskService
) -> None:
    add_project(store)
    task = service.create_task(task_data("Old"))

    updated = service.replace_task(
        task.id,
        TaskInput(
            title="Updated",
            description="Updated description",
            completed=True,
            project_id=1,
        ),
    )

    assert updated.title == "Updated"
    assert updated.description == "Updated description"
    assert updated.completed is True


def test_delete_task_removes_task(
    store: InMemoryStore, service: InMemoryTaskService
) -> None:
    add_project(store)
    task = service.create_task(task_data("Delete me"))

    service.delete_task(task.id)

    assert service.list_tasks() == []
