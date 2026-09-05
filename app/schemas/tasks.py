"""Request and response schemas for the Task resource."""

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    """Define fields shared by every Task schema."""

    # These type hints and Field constraints validate data at runtime and also
    # become part of the OpenAPI contract displayed by Swagger UI.
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )

    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    completed: bool = False
    project_id: int = Field(gt=0)


class TaskInput(TaskBase):
    """Validate client-controlled fields for a Task create or replacement."""


class TaskResponse(TaskBase):
    """Describe a Task returned by the API."""

    id: int = Field(gt=0)
