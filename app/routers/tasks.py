"""HTTP endpoints for the Task resource."""

from fastapi import APIRouter, Body, HTTPException, Response, status

from app.routers.projects import find_project
from app.storage import Task, tasks

# Tasks use the same collection and item URL pattern as Projects.
router = APIRouter(prefix="/tasks", tags=["Tasks"])


def find_task(task_id: int) -> Task:
    """Find one task or return an HTTP 404 error to the client."""
    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Task not found",
    )


# GET /tasks reads the entire Task collection.
@router.get("", summary="List all tasks")
def list_tasks() -> list[Task]:
    """Return every task currently stored in memory."""
    return tasks


# GET /tasks/{task_id} reads one Task identified by its path parameter.
@router.get("/{task_id}", summary="Get one task")
def get_task(task_id: int) -> Task:
    """Return the task with the requested ID."""
    return find_task(task_id)


# A Task can be created only when its related Project exists.
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(
    title: str = Body(),
    description: str = Body(),
    completed: bool = Body(),
    project_id: int = Body(),
) -> Task:
    """Create a task associated with an existing project."""
    find_project(project_id)
    next_task_id = max((int(task["id"]) for task in tasks), default=0) + 1

    task: Task = {
        "id": next_task_id,
        "title": title,
        "description": description,
        "completed": completed,
        "project_id": project_id,
    }
    tasks.append(task)
    return task


# PUT replaces all editable Task values, including its Project relationship.
@router.put("/{task_id}", summary="Replace a task")
def replace_task(
    task_id: int,
    title: str = Body(),
    description: str = Body(),
    completed: bool = Body(),
    project_id: int = Body(),
) -> Task:
    """Replace an existing task after checking its related project."""
    task = find_task(task_id)
    find_project(project_id)
    task.update(
        title=title,
        description=description,
        completed=completed,
        project_id=project_id,
    )
    return task


# A successful DELETE removes the Task and returns no response body.
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(task_id: int) -> Response:
    """Remove a task from the in-memory collection."""
    task = find_task(task_id)
    tasks.remove(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
