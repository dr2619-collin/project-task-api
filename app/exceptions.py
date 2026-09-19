"""Application outcomes raised by services without depending on FastAPI."""


class ProjectNotFoundError(Exception):
    """Signal that the requested Project does not exist.

    This exception remains outside the router package so the service can be
    reused by HTTP routes, jobs, or message consumers without importing FastAPI.
    """


class TaskNotFoundError(Exception):
    """Signal that the requested Task does not exist."""


class ProjectHasTasksError(Exception):
    """Signal that a Project cannot be deleted while Tasks reference it."""
