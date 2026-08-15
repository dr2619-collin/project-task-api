"""PostgreSQL integration tests for every TaskRepository method and ORM relation."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.projects import ProjectCreate
from app.schemas.tasks import TaskCreate, TaskUpdate


def test_list_all_returns_tasks_in_id_order(db_session: Session) -> None:
    """list_all persists and returns Tasks in the repository's declared order."""
    project = create_project(db_session, "Course API")
    repository = TaskRepository(db_session)
    first = create_task(repository, db_session, project.id, "First Task")
    second = create_task(repository, db_session, project.id, "Second Task")

    tasks = repository.list_all()

    assert [task.id for task in tasks] == [first.id, second.id]


def test_list_by_project_filters_related_tasks(db_session: Session) -> None:
    """list_by_project returns only Tasks belonging to the requested Project."""
    first_project = create_project(db_session, "First Project")
    second_project = create_project(db_session, "Second Project")
    repository = TaskRepository(db_session)
    first_task = create_task(repository, db_session, first_project.id, "First Task")
    create_task(repository, db_session, second_project.id, "Second Task")

    tasks = repository.list_by_project(first_project.id)

    assert [task.id for task in tasks] == [first_task.id]
    assert all(task.project_id == first_project.id for task in tasks)


def test_get_by_id_returns_existing_task_and_none_when_missing(
    db_session: Session,
) -> None:
    """get_by_id distinguishes a persisted Task from an absent ID."""
    project = create_project(db_session, "Course API")
    repository = TaskRepository(db_session)
    created = create_task(repository, db_session, project.id, "Stored Task")

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.title == "Stored Task"
    assert repository.get_by_id(999) is None


def test_exists_for_project_reports_related_task_presence(db_session: Session) -> None:
    """exists_for_project changes from false to true after Task creation."""
    project = create_project(db_session, "Course API")
    repository = TaskRepository(db_session)

    assert repository.exists_for_project(project.id) is False

    create_task(repository, db_session, project.id, "Stored Task")

    assert repository.exists_for_project(project.id) is True


def test_create_persists_task_and_generates_id(db_session: Session) -> None:
    """create maps Task request data to a PostgreSQL row with a generated ID."""
    project = create_project(db_session, "Course API")
    repository = TaskRepository(db_session)

    created = repository.create(
        TaskCreate(
            title="Created Task",
            description="Created by repository.",
            completed=True,
            project_id=project.id,
        )
    )
    db_session.commit()

    assert created.id > 0
    stored = repository.get_by_id(created.id)
    assert stored is not None
    assert stored.completed is True
    assert stored.project_id == project.id


def test_replace_updates_all_editable_task_columns(db_session: Session) -> None:
    """replace updates Task fields, including its Project relationship ID."""
    original_project = create_project(db_session, "Original Project")
    replacement_project = create_project(db_session, "Replacement Project")
    repository = TaskRepository(db_session)
    task = create_task(repository, db_session, original_project.id, "Original Task")

    updated = repository.replace(
        task,
        TaskUpdate(
            title="Updated Task",
            description="Updated description.",
            completed=True,
            project_id=replacement_project.id,
        ),
    )
    db_session.commit()
    db_session.refresh(updated)

    assert updated.title == "Updated Task"
    assert updated.description == "Updated description."
    assert updated.completed is True
    assert updated.project_id == replacement_project.id


def test_delete_removes_persisted_task(db_session: Session) -> None:
    """delete removes a Task row after its transaction is committed."""
    project = create_project(db_session, "Course API")
    repository = TaskRepository(db_session)
    task = create_task(repository, db_session, project.id, "Deleted Task")

    repository.delete(task)
    db_session.commit()

    assert repository.get_by_id(task.id) is None


def test_create_enforces_task_project_foreign_key(db_session: Session) -> None:
    """The Task ORM mapping cannot persist a nonexistent Project reference."""
    repository = TaskRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            TaskCreate(
                title="Orphan Task",
                description="This Project does not exist.",
                project_id=999,
            )
        )

    db_session.rollback()


# HELPERS


def create_project(session: Session, name: str):
    """Create a persisted parent Project for Task repository scenarios."""
    repository = ProjectRepository(session)
    project = repository.create(
        ProjectCreate(name=name, description=f"Description for {name}.")
    )
    session.commit()
    session.refresh(project)
    return project


def create_task(
    repository: TaskRepository,
    session: Session,
    project_id: int,
    title: str,
):
    """Create and commit one Task used by a repository test."""
    task = repository.create(
        TaskCreate(
            title=title,
            description=f"Description for {title}.",
            project_id=project_id,
        )
    )
    session.commit()
    session.refresh(task)
    return task
