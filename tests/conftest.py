"""Shared pytest fixtures for PostgreSQL-backed API integration tests.

Pytest discovers a file named conftest.py automatically. Test modules do not
import these fixtures. Instead, a test requests one by adding its name as a
function parameter, such as ``client`` or ``db_session``.

Fixture dependency flow for an API integration test:

    client -> reset_database -> test_engine -> postgres_container

Fixture dependency flow for a repository integration test:

    db_session -> reset_database -> test_engine -> postgres_container
"""

import os
from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start one disposable PostgreSQL database for the entire pytest session."""
    # scope="session" means one container for one `uv run pytest` command, not
    # one container per test file. Pytest creates it only if a test requests a
    # fixture that depends on it; unit tests do not start Docker.
    #
    # Testcontainers communicates with Docker Desktop, starts postgres:18, and
    # waits until PostgreSQL is ready to accept connections.
    # driver="psycopg" makes the generated SQLAlchemy URL use this project's
    # Psycopg 3 driver instead of the Testcontainers default Psycopg 2 driver.
    with PostgresContainer(
        "postgres:18",
        username="postgres",
        password="postgres",
        dbname="project_task_test",
        driver="psycopg",
    ) as container:
        # Set this before importing app.database.session. That module reads
        # DATABASE_URL when it creates its module-level SQLAlchemy engine.
        # Therefore, the application connects to this temporary database rather
        # than the local development database named project_task.
        os.environ["DATABASE_URL"] = container.get_connection_url()

        # `yield container` pauses this fixture while every test that needs the
        # session-scoped container runs. Pytest resumes below only after the
        # entire pytest command has finished.
        yield container

    # Leaving the `with PostgresContainer(...)` block stops and removes the
    # temporary Docker container. Remove the test-only environment value too.
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session")
def test_engine(postgres_container: PostgresContainer) -> Engine:
    """Return the application engine configured for the temporary container."""
    # Requesting postgres_container as a parameter forces pytest to complete
    # that fixture first. DATABASE_URL is therefore set before these imports.
    # Importing the models registers Project and Task with Base.metadata before
    # the table fixture creates the schema in the temporary database.
    from app import models  # noqa: F401
    from app.database.session import engine

    # This is the application's normal engine. It is not a separate test-only
    # engine; it points at the Testcontainers URL because of the import order.
    return engine


@pytest.fixture
def reset_database(test_engine: Engine) -> Generator[None, None, None]:
    """Give each integration test empty Project and Task tables."""
    from app.database.base import Base

    # Setup for one test function: remove any data/schema from an earlier test,
    # then create empty tables using the real ORM metadata.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Plain `yield` gives no value to the test. It marks the boundary between
    # setup above and cleanup below: pytest runs the test while this fixture is
    # paused here, then resumes at the next line even if the test fails.
    yield

    # Cleanup after the one test function. The PostgreSQL container stays alive
    # for later tests, but no test data or tables are shared between them.
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(reset_database: None) -> Generator[Session, None, None]:
    """Provide one real SQLAlchemy Session for a repository integration test."""
    # Requesting reset_database ensures the Testcontainers database is ready
    # and empty before this real database Session is created.
    # reset_database depends on test_engine, so this import happens only after
    # the application engine points to the temporary PostgreSQL container.
    from app.database.session import session_factory

    with session_factory() as session:
        # `yield session` gives the repository test a real SQLAlchemy Session.
        # Repository tests call SQLAlchemy and PostgreSQL directly; FastAPI is
        # not started for them because they do not request the `client` fixture.
        yield session
        # A test may intentionally trigger a database error. Roll back any
        # uncommitted transaction before reset_database drops the tables.
        session.rollback()


@pytest.fixture
def client(reset_database: None) -> Generator[TestClient, None, None]:
    """Provide a TestClient after the temporary database is ready."""
    # Requesting reset_database ensures the Testcontainers database is ready
    # and empty before FastAPI starts.
    # TestClient runs the FastAPI lifespan, just as an application startup does.
    # At this point DATABASE_URL already points to the Testcontainers database.
    from app.main import app

    with TestClient(app) as test_client:
        # Entering this context starts FastAPI's lifespan function. It does not
        # start Uvicorn, bind localhost:8000, or make a real network connection.
        # TestClient sends ASGI requests directly to this in-process FastAPI app.
        yield test_client

    # Leaving this context closes TestClient and runs FastAPI lifespan cleanup.


@pytest.fixture
def member_headers() -> dict[str, str]:
    """Provide the Authorization header for the course-demo member role."""
    from app.auth.users import Role, demo_token_for

    return {"Authorization": f"Bearer {demo_token_for(Role.MEMBER)}"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    """Provide the Authorization header for the course-demo administrator role."""
    from app.auth.users import Role, demo_token_for

    return {"Authorization": f"Bearer {demo_token_for(Role.ADMIN)}"}


@pytest.fixture
def admin_client(
    client: TestClient,
    admin_headers: dict[str, str],
) -> TestClient:
    """Provide the per-test API client configured as an administrator.

    The ordinary ``client`` fixture stays unauthenticated so Module 08 tests
    can explicitly verify missing-token behavior. Each test receives a fresh
    TestClient, so setting these default headers cannot affect another test.
    """
    client.headers.update(admin_headers)
    return client


@pytest.fixture
def member_client(
    client: TestClient,
    member_headers: dict[str, str],
) -> TestClient:
    """Provide the per-test API client configured as a member.

    Each test receives a fresh TestClient, so setting this default header does
    not affect the ordinary unauthenticated client or administrator tests.
    """
    client.headers.update(member_headers)
    return client
