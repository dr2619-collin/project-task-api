"""Shared in-memory state for the alternative service implementations."""

from dataclasses import dataclass, field
from threading import RLock

from app.models.project import Project
from app.models.task import Task


@dataclass
class InMemoryStore:
    """Hold Projects and Tasks for one application-scoped in-memory service pair."""

    projects: list[Project] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    # One process-local lock protects compound operations such as ID
    # generation, relationship checks, and list mutation.
    lock: RLock = field(default_factory=RLock, repr=False)
