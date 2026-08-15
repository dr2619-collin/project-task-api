"""PostgreSQL integration tests for every ProjectRepository method."""

from sqlalchemy.orm import Session

from app.repositories.projects import ProjectRepository
from app.schemas.projects import ProjectCreate, ProjectUpdate


def test_list_all_returns_projects_in_id_order(db_session: Session) -> None:
    """list_all persists and returns Projects in the repository's declared order."""
    repository = ProjectRepository(db_session)
    first = create_project(repository, db_session, "First Project")
    second = create_project(repository, db_session, "Second Project")

    projects = repository.list_all()

    assert [project.id for project in projects] == [first.id, second.id]


def test_get_by_id_returns_existing_project_and_none_when_missing(
    db_session: Session,
) -> None:
    """get_by_id distinguishes a persisted Project from an absent ID."""
    repository = ProjectRepository(db_session)
    created = create_project(repository, db_session, "Stored Project")

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Stored Project"
    assert repository.get_by_id(999) is None


def test_create_persists_project_and_generates_id(db_session: Session) -> None:
    """create maps request data to a PostgreSQL row with a generated ID."""
    repository = ProjectRepository(db_session)

    created = repository.create(
        ProjectCreate(name="Created Project", description="Created by repository.")
    )
    db_session.commit()

    assert created.id > 0
    stored = repository.get_by_id(created.id)
    assert stored is not None
    assert stored.name == "Created Project"
    assert stored.description == "Created by repository."


def test_replace_updates_persisted_project(db_session: Session) -> None:
    """replace changes both editable Project columns in PostgreSQL."""
    repository = ProjectRepository(db_session)
    project = create_project(repository, db_session, "Original Project")

    updated = repository.replace(
        project,
        ProjectUpdate(name="Updated Project", description="Updated description."),
    )
    db_session.commit()
    db_session.refresh(updated)

    assert updated.name == "Updated Project"
    assert updated.description == "Updated description."


def test_delete_removes_persisted_project(db_session: Session) -> None:
    """delete removes a Project row after its transaction is committed."""
    repository = ProjectRepository(db_session)
    project = create_project(repository, db_session, "Deleted Project")

    repository.delete(project)
    db_session.commit()

    assert repository.get_by_id(project.id) is None


# HELPERS


def create_project(repository: ProjectRepository, session: Session, name: str):
    """Create and commit one Project used by a repository test."""
    project = repository.create(
        ProjectCreate(name=name, description=f"Description for {name}.")
    )
    session.commit()
    session.refresh(project)
    return project
