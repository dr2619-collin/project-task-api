"""Pydantic response models for the Module 09 async I/O demonstration."""

from typing import Literal

from pydantic import BaseModel, Field


class WaitResponse(BaseModel):
    """Describe one completed simulated I/O wait."""

    mode: Literal["sync", "async"] = Field(
        description="Whether the route used synchronous or asynchronous waiting."
    )
    waited_seconds: float = Field(
        ge=0,
        description="The requested duration of the simulated I/O wait.",
    )
    message: str = Field(
        description="A short explanation of the completed demonstration.",
    )
