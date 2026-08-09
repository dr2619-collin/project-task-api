"""Application exceptions raised by the service layer."""


class ProjectNotFoundError(Exception):
    """The requested Project does not exist."""


class TaskNotFoundError(Exception):
    """The requested Task does not exist."""


class ProjectHasTasksError(Exception):
    """A Project cannot be deleted while Tasks reference it."""
