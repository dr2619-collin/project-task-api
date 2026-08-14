# Database Sessions and Connection Pooling

This guide explains how the Module 05 application reaches PostgreSQL and how SQLAlchemy manages request-scoped database work.

## Main objects

| SQLAlchemy object | Purpose | Comparable Java concept |
|---|---|---|
| `engine` | Owns the database connection pool. | `DataSource` / JDBC connection pool |
| database connection | A live network connection to PostgreSQL. | `java.sql.Connection` |
| `Session` | Tracks ORM objects and one unit of work. | JPA `EntityManager` or Hibernate `Session` |
| `session_factory` | A callable factory that creates `Session` objects. | `EntityManagerFactory` creating an `EntityManager` |

## Why ORM models inherit `DeclarativeBase`

Every ORM model inherits the shared `Base` class:

```python
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
```

`DeclarativeBase` gives SQLAlchemy a shared model registry and `Base.metadata`. As models declare table names, columns, primary keys, foreign keys, and indexes, SQLAlchemy adds those definitions to `Base.metadata`.

At API startup, this course project runs:

```python
Base.metadata.create_all(bind=engine)
```

SQLAlchemy uses the metadata to create missing tables and database constraints. It does not alter an existing table when a model later changes. Production applications use versioned database migrations, often Alembic, for later schema changes.

## Request-scoped Sessions

FastAPI dependency injection creates one Session for each request that needs one:

```python
DatabaseSession = Annotated[Session, Depends(get_db)]
```

This annotation means: “this parameter is a SQLAlchemy `Session`; FastAPI should obtain it by calling `get_db`.” A route receives it like this:

```python
def create_project(data: ProjectCreate, session: DatabaseSession) -> Project:
    return ProjectService(session).create_project(data)
```

FastAPI calls `get_db`; the router passes the Session to the service; the service passes the same Session to repositories. The router does not execute SQL. The service coordinates a use case and transaction; repositories execute queries and writes.

```text
FastAPI → Router → Service → Repository → Session → PostgreSQL
```

## The `get_db` generator

```python
def get_db() -> Generator[Session, None, None]:
    with session_factory() as session:
        yield session
```

The sequence is:

1. `session_factory()` creates a new Session.
2. `yield session` gives that Session to FastAPI and pauses the generator.
3. FastAPI runs the route, service, and repository code.
4. When the request finishes, the generator resumes.
5. The `with` block closes the Session, returning any borrowed connection to the pool.

Closing the Session does not commit changes. Services explicitly call `commit()` when work succeeds or `rollback()` when it fails.

## Session versus connection

A Session is not a permanent one-to-one database connection. It is a unit of work that borrows a connection from the Engine's pool only when database work is required.

```text
Request starts
    ↓
Session created (no connection necessarily borrowed yet)
    ↓
First query or write
    ↓
Session borrows a PostgreSQL connection from the pool
    ↓
Service commits or rolls back
    ↓
Session closes; connection returns to the pool
```

During a typical request that performs database work, one Session uses one borrowed connection. That connection is not permanently assigned to the Session; it is returned when the Session closes. A Session can also work with more than one connection in advanced multi-database scenarios, but this course project uses one database Engine.

## Transactions

SQLAlchemy starts a transaction automatically when the Session first performs database work. The service controls the result:

```python
try:
    project = self.project_repository.create(data)
    self.session.commit()
    return project
except Exception:
    self.session.rollback()
    raise
```

`flush()` sends pending SQL to PostgreSQL so generated values, such as an ID, are available. It does not make the change permanent. `commit()` makes the transaction durable; `rollback()` discards its uncommitted changes.

## Default connection-pool settings

The application creates its Engine with:

```python
engine = create_engine(DATABASE_URL)
```

For PostgreSQL, SQLAlchemy’s default `QueuePool` settings are:

| Setting | Default | Meaning |
|---|---:|---|
| `pool_size` | 5 | Connections kept in the pool after use. |
| `max_overflow` | 10 | Extra temporary connections allowed during busy periods. |
| Maximum concurrent connections | 15 | `pool_size + max_overflow`. |
| `pool_timeout` | 30 seconds | How long to wait for a connection when the pool is full. |

The pool starts empty and opens connections only as needed. If all 15 connections are in use, another Session that needs database access waits up to 30 seconds. If no connection becomes available, SQLAlchemy raises a pool timeout error.

The limit applies per application process or pod. Four pods with the default settings could use up to 60 PostgreSQL connections.

## Configuring pool settings

Pool settings are not automatically read from `.env`. `create_engine()` must be explicitly given the settings.

For this project, environment variables would be a good approach because each environment can choose values without changing source code.

Add settings to `.env`:

```text
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT_SECONDS=30
```

Then configure the Engine in `app/database/session.py`:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "30")),
)
```

For this small local course project, the default values are appropriate. Before changing settings in a deployed application, account for the number of pods, worker processes, database connection limits, and how long requests hold transactions open.

## Source

- [SQLAlchemy connection pooling documentation](https://docs.sqlalchemy.org/21/core/pooling.html)
- [SQLAlchemy engine configuration documentation](https://docs.sqlalchemy.org/21/core/engines.html)
