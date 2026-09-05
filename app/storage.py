"""Temporary in-memory storage shared by the API routers."""

from typing import TypeAlias

# Module 02 uses dictionaries instead of Pydantic models. Request and response
# models will give these resources stronger types in Module 03.
Project: TypeAlias = dict[str, int | str]
Task: TypeAlias = dict[str, int | str | bool]

# These lists reset whenever the application restarts. A database and
# repository layer will replace them in a later module.
projects: list[Project] = [
    {
        "id": 1,
        "name": "Course API",
        "description": "Build the course demonstration API.",
    }
]

tasks: list[Task] = [
    {
        "id": 1,
        "title": "Create the first endpoint",
        "description": "Add a welcome endpoint to the FastAPI application.",
        "completed": True,
        "project_id": 1,
    }
]
