"""HTTP endpoints for the Task resource."""

from fastapi import APIRouter, HTTPException, Response, status

from app.routers.projects import find_project
from app.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate
from app.storage import tasks

# Tasks use the same collection and item URL pattern as Projects.
router = APIRouter(prefix="/tasks", tags=["Tasks"])


def find_task(task_id: int) -> TaskResponse:
    """Find one task or return an HTTP 404 error to the client."""
    for task in tasks:
        if task.id == task_id:
            return task

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Task not found",
    )


# GET /tasks reads the entire Task collection.
@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List all tasks",
    description="Return every task currently stored by the application.",
)
def list_tasks() -> list[TaskResponse]:
    """Return every task currently stored in memory."""
    return tasks


# GET /tasks/{task_id} reads one Task identified by its path parameter.
@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get one task",
    description="Return the task identified by the path parameter.",
    responses={404: {"description": "Task not found"}},
)
def get_task(task_id: int) -> TaskResponse:
    """Return the task with the requested ID."""
    return find_task(task_id)


# A Task can be created only when its related Project exists.
@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description="Create a task and associate it with an existing project.",
    responses={404: {"description": "Related project not found"}},
)
def create_task(data: TaskCreate) -> TaskResponse:
    """Create a task associated with an existing project."""
    # FastAPI validates TaskCreate before this function runs and uses the same
    # schema in OpenAPI. This application-level check then confirms that the
    # related Project resource actually exists.
    find_project(data.project_id)
    next_task_id = max((task.id for task in tasks), default=0) + 1

    task = TaskResponse(
        id=next_task_id,
        **data.model_dump(),
    )
    tasks.append(task)
    return task


# PUT replaces all editable Task values, including its Project relationship.
@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Replace a task",
    description="Replace all editable fields and verify the related project.",
    responses={
        404: {"description": "Task or related project not found"},
    },
)
def replace_task(
    task_id: int,
    data: TaskUpdate,
) -> TaskResponse:
    """Replace an existing task after checking its related project."""
    task = find_task(task_id)
    find_project(data.project_id)
    updated_task = TaskResponse(
        id=task_id,
        **data.model_dump(),
    )
    tasks[tasks.index(task)] = updated_task
    return updated_task


# A successful DELETE removes the Task and returns no response body.
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete the task identified by the path parameter.",
    responses={404: {"description": "Task not found"}},
)
def delete_task(task_id: int) -> Response:
    """Remove a task from the in-memory collection."""
    task = find_task(task_id)
    tasks.remove(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
