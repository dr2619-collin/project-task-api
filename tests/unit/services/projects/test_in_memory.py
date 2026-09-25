"""Unit tests for the in-memory Project service contract."""

import pytest

from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.task import Task
from app.schemas.projects import ProjectInput
from app.services.in_memory_store import InMemoryStore
from app.services.projects import InMemoryProjectService


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def service(store: InMemoryStore) -> InMemoryProjectService:
    return InMemoryProjectService(store)


def project_data(name: str = "Course API") -> ProjectInput:
    return ProjectInput(name=name, description="Course demonstration")


def test_create_list_and_get_project(service: InMemoryProjectService) -> None:
    created = service.create_project(project_data())

    assert created.id == 1
    assert service.list_projects() == [created]
    assert service.get_project(created.id) is created


def test_get_project_raises_for_missing_id(service: InMemoryProjectService) -> None:
    with pytest.raises(ProjectNotFoundError):
        service.get_project(999)


def test_replace_project_updates_fields(service: InMemoryProjectService) -> None:
    project = service.create_project(project_data())

    updated = service.replace_project(
        project.id,
        ProjectInput(name="Updated API", description="Updated description"),
    )

    assert updated is project
    assert updated.name == "Updated API"
    assert updated.description == "Updated description"


def test_list_project_tasks_requires_existing_project(
    service: InMemoryProjectService,
) -> None:
    with pytest.raises(ProjectNotFoundError):
        service.list_project_tasks(999)


def test_list_project_tasks_returns_related_tasks(
    store: InMemoryStore, service: InMemoryProjectService
) -> None:
    project = service.create_project(project_data())
    task = Task(
        id=1,
        title="Task",
        description="Related task",
        completed=False,
        project_id=project.id,
    )
    store.tasks.append(task)

    assert service.list_project_tasks(project.id) == [task]


def test_delete_project_rejects_related_tasks(
    store: InMemoryStore, service: InMemoryProjectService
) -> None:
    project = service.create_project(project_data())
    store.tasks.append(
        Task(
            id=1,
            title="Task",
            description="Related task",
            completed=False,
            project_id=project.id,
        )
    )

    with pytest.raises(ProjectHasTasksError):
        service.delete_project(project.id)

    assert service.get_project(project.id) is project


def test_delete_project_removes_project_without_tasks(
    service: InMemoryProjectService,
) -> None:
    project = service.create_project(project_data())

    service.delete_project(project.id)

    assert service.list_projects() == []
