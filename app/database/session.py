"""PostgreSQL engine and request-scoped SQLAlchemy sessions."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Keep connection details outside source code. The development command loads
# DATABASE_URL from .env before importing the application.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/project_task",
)
# Set DATABASE_ECHO_SQL=true in .env to print generated SQL in the development
# server terminal. Keep it false normally because SQL logs can be noisy.
ECHO_SQL = os.getenv("DATABASE_ECHO_SQL", "false").lower() == "true"

# The engine owns the database connection pool. Creating it does not immediately
# connect; SQLAlchemy borrows a connection from this pool when a Session first
# performs database work.
engine = create_engine(DATABASE_URL, echo=ECHO_SQL)

# session_factory is a callable factory, not one shared Session. Calling it
# creates a new Session object: session = session_factory().
#
# bind=engine: sessions created by this factory use this engine's connection pool.
# autoflush=False: pending changes are not automatically sent before every query;
#                  this project calls session.flush() explicitly in repositories.
# expire_on_commit=False: ORM objects keep their loaded attribute values after
#                         commit, so the service can return them without an
#                         immediate refresh query. It does not make the values
#                         permanently current if another request later changes them.
session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy Session for one HTTP request.

    FastAPI calls this dependency for route parameters declared with
    Depends(get_db). It receives the yielded Session, runs the route and service
    code, then resumes this generator after the response work is complete.
    """
    # Calling the factory creates one Session (a unit of work and identity map),
    # not a permanent database connection. The Session borrows a connection from
    # the engine pool only when it needs one for database work.
    with session_factory() as session:
        # Pause here and give the Session to FastAPI. After the route finishes—
        # even if it raises an exception—execution resumes and the context manager
        # closes the Session, returning any borrowed connection to the pool.
        # Closing a Session does not commit changes; services commit or roll back.
        yield session
