"""Unit tests for every Task Pydantic schema and declared rule."""

import pytest
from pydantic import ValidationError

from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate


@pytest.mark.parametrize("missing_field", ["title", "description", "project_id"])
def test_task_create_requires_each_declared_required_field(missing_field: str) -> None:
    """A create request must include every required Task field."""
    data = valid_task_data()
    data.pop(missing_field)

    with pytest.raises(ValidationError):
        TaskCreate(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("title", "   "),
        ("description", "   "),
        ("title", "t" * 121),
        ("description", "d" * 501),
        ("project_id", 0),
        ("project_id", -1),
    ],
)
def test_task_create_enforces_field_boundaries(
    field_name: str,
    value: int | str,
) -> None:
    """Task fields must satisfy their declared constraints."""
    data = valid_task_data()
    data[field_name] = value

    with pytest.raises(ValidationError):
        TaskCreate(**data)


def test_task_create_accepts_declared_maximum_lengths_and_positive_id() -> None:
    """The inclusive limits and a positive Project ID remain valid values."""
    task = TaskCreate(
        title="t" * 120,
        description="d" * 500,
        project_id=1,
    )

    assert len(task.title) == 120
    assert len(task.description) == 500
    assert task.project_id == 1


def test_task_create_defaults_completed_to_false() -> None:
    """A new Task is incomplete unless the client explicitly marks it complete."""
    task = TaskCreate(**valid_task_data())

    assert task.completed is False


def test_task_create_strips_whitespace_and_rejects_undocumented_field() -> None:
    """The Task request contract normalizes strings and forbids extra input."""
    task = TaskCreate(
        title="  Write tests  ",
        description="  Add schema unit tests.  ",
        project_id=1,
    )

    assert task.title == "Write tests"
    assert task.description == "Add schema unit tests."

    with pytest.raises(ValidationError):
        TaskCreate(**valid_task_data(), priority="high")


def test_task_update_uses_the_same_request_contract() -> None:
    """A replacement request inherits Task field rules and configuration."""
    task = TaskUpdate(
        title="  Update tests  ",
        description="  Replace every editable field.  ",
        completed=True,
        project_id=1,
    )

    assert task.title == "Update tests"
    assert task.description == "Replace every editable field."
    assert task.completed is True


def test_task_response_reads_an_orm_task() -> None:
    """The response schema serializes attributes from an ORM model instance."""
    source = Task(
        id=1,
        title="Write tests",
        description="Add schema unit tests.",
        completed=False,
        project_id=1,
    )

    response = TaskResponse.model_validate(source)

    assert response.model_dump() == {
        "title": "Write tests",
        "description": "Add schema unit tests.",
        "completed": False,
        "project_id": 1,
        "id": 1,
    }


def test_task_response_rejects_nonpositive_server_id() -> None:
    """A response must contain a positive server-generated identifier."""
    with pytest.raises(ValidationError):
        TaskResponse(**valid_task_data(), id=0)


# HELPERS


def valid_task_data() -> dict[str, int | str]:
    """Return a valid Task request body for focused validation scenarios."""
    return {
        "title": "Write tests",
        "description": "Add schema unit tests.",
        "project_id": 1,
    }
