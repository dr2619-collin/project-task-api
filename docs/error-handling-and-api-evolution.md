# Error Handling and API Evolution

Module 10 gives API failures a consistent response format and introduces a
versioned path for Project and Task operations. The business and persistence
layers remain responsible for their existing rules.

## Represent errors with Problem Details

The API returns errors using the RFC 9457 `application/problem+json` media type.
Each response includes a stable problem type, a short title, the HTTP status,
an occurrence-specific detail, and the request path (`instance`). Validation
responses also include an `errors` array with field-level information.

```json
{
  "type": "https://project-task-api.local/problems/project-not-found",
  "title": "Project not found",
  "status": 404,
  "detail": "No Project exists with id 42.",
  "instance": "/api/v1/projects/42"
}
```

Services raise application exceptions such as `ProjectNotFoundError` and
`ProjectHasTasksError`. These inherit from `DomainError`, which carries the
problem type, title, and HTTP status meaning without importing FastAPI. A
central handler in `app/error_handlers.py` converts domain, HTTP, validation,
and unexpected failures into the common response format. Routers do not catch
each domain exception themselves. Unexpected failures receive a generic 500
response that avoids exposing implementation details; the ASGI server reports
the uncaught exception in its server output.

The same response metadata is included in OpenAPI so clients can inspect the
expected error format in Swagger UI, ReDoc, or `/openapi.json`.

## Evolve paths with a versioned API

Project and Task operations are available under `/api/v1`. The original
unversioned paths remain temporarily available and are marked deprecated in
OpenAPI. Responses from those legacy paths include `Deprecation`, `Sunset`, and
`Link` headers that point clients to the corresponding `/api/v1` path.

For example:

```text
GET /projects/3       # legacy; includes migration headers
GET /api/v1/projects/3 # versioned path
```

Both paths use the same routers, authentication rules, services, and data.
The versioned prefix is therefore a migration path, not a second
implementation. New clients should use `/api/v1`.
