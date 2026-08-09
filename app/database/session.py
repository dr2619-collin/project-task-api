"""PostgreSQL engine and request-scoped SQLAlchemy sessions."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Keep connection details outside source code. The development command loads
# DATABASE_URL from .env before importing the application.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/project_task_api",
)

# The engine owns the database connection pool. Creating it does not immediately
# connect; SQLAlchemy opens connections when the application performs DB work.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session for one HTTP request."""
    with SessionLocal() as session:
        yield session
