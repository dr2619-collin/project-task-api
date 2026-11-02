"""Application outcomes raised by services without depending on FastAPI."""


class DomainError(Exception):
    """Base class for business failures that have a documented HTTP meaning."""

    problem_type = "domain-error"
    title = "Domain error"
    status_code = 400
    default_detail = "The requested operation could not be completed."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class ProjectNotFoundError(DomainError):
    """Signal that the requested Project does not exist.

    This exception remains outside the router package so the service can be
    reused by HTTP routes, jobs, or message consumers without importing FastAPI.
    """

    problem_type = "project-not-found"
    title = "Project not found"
    status_code = 404
    default_detail = "The requested project does not exist."


class TaskNotFoundError(DomainError):
    """Signal that the requested Task does not exist."""

    problem_type = "task-not-found"
    title = "Task not found"
    status_code = 404
    default_detail = "The requested task does not exist."


class ProjectHasTasksError(DomainError):
    """Signal that a Project cannot be deleted while Tasks reference it."""

    problem_type = "project-has-tasks"
    title = "Project has related tasks"
    status_code = 409
    default_detail = "Delete the project's tasks before deleting the project."
