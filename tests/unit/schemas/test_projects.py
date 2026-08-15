"""Unit tests for every Project Pydantic schema and declared rule."""

import pytest
from pydantic import ValidationError

from app.models.project import Project
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate


@pytest.mark.parametrize("missing_field", ["name", "description"])
def test_project_create_requires_each_declared_field(missing_field: str) -> None:
    """A create request must include both Project fields."""
    data = valid_project_data()
    data.pop(missing_field)

    with pytest.raises(ValidationError):
        ProjectCreate(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("name", "   "),
        ("description", "   "),
        ("name", "n" * 101),
        ("description", "d" * 501),
    ],
)
def test_project_create_enforces_field_boundaries(
    field_name: str,
    value: str,
) -> None:
    """Project names and descriptions must satisfy their declared constraints."""
    data = valid_project_data()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ProjectCreate(**data)


def test_project_create_accepts_declared_maximum_lengths() -> None:
    """The inclusive maximum lengths remain valid request values."""
    project = ProjectCreate(name="n" * 100, description="d" * 500)

    assert len(project.name) == 100
    assert len(project.description) == 500


def test_project_create_strips_surrounding_whitespace() -> None:
    """Shared schema configuration normalizes string input."""
    project = ProjectCreate(
        name="  Testing Module  ",
        description="  Add automated tests.  ",
    )

    assert project.name == "Testing Module"
    assert project.description == "Add automated tests."


def test_project_create_rejects_undocumented_field() -> None:
    """The request contract rejects input outside the documented schema."""
    with pytest.raises(ValidationError):
        ProjectCreate(**valid_project_data(), owner="Instructor")


def test_project_update_uses_the_same_request_contract() -> None:
    """A replacement request inherits Project field rules and configuration."""
    project = ProjectUpdate(
        name="  Updated Module  ",
        description="  Replace every editable field.  ",
    )

    assert project.name == "Updated Module"
    assert project.description == "Replace every editable field."


def test_project_response_reads_an_orm_project() -> None:
    """The response schema serializes attributes from an ORM model instance."""
    source = Project(id=1, name="Course API", description="Course demonstration")

    response = ProjectResponse.model_validate(source)

    assert response.model_dump() == {
        "name": "Course API",
        "description": "Course demonstration",
        "id": 1,
    }


def test_project_response_rejects_nonpositive_server_id() -> None:
    """A response must contain a positive server-generated identifier."""
    with pytest.raises(ValidationError):
        ProjectResponse(**valid_project_data(), id=0)


# HELPERS


def valid_project_data() -> dict[str, str]:
    """Return a valid Project request body for focused validation scenarios."""
    return {"name": "Testing Module", "description": "Add schema unit tests."}
