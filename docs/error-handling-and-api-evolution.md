# Error Handling and API Evolution

Before Module 10, the API could reject a request for several different
reasons. Those failures originate in different parts of the application:

- A service can determine that a Project or Task does not exist, or that a
  Project cannot be deleted while Tasks still reference it.
- An authentication or authorization dependency can reject a request with
  `401` or `403`.
- FastAPI and Pydantic can reject invalid JSON, missing fields, invalid field
  values, or an invalid typed path parameter.
- FastAPI can reject an unknown path with `404`.
- Unexpected programming or infrastructure failures can occur anywhere.

Without an explicit policy, each source can produce its own response shape.
Clients would need to learn several formats, and an unexpected error could
expose details that belong only in server diagnostics. Module 10 keeps the
sources of these failures separate, but gives their HTTP responses one
consistent structure.

## Map each error source to a handler

`app/error_handlers.py` registers one handler for each category of error:

| Error source | Example | Exception type | Registered handler | Client outcome |
| --- | --- | --- | --- | --- |
| Application rule | Requested Project does not exist | `ProjectNotFoundError` | `handle_domain_error` | `404` Problem Details |
| Application rule | Delete a Project that still has Tasks | `ProjectHasTasksError` | `handle_domain_error` | `409` Problem Details |
| HTTP boundary | Missing Bearer token or forbidden write | `StarletteHTTPException` | `handle_http_exception` | `401` or `403` Problem Details |
| Framework validation | Blank name, missing field, or invalid path ID | `RequestValidationError` | `handle_validation_error` | `422` Problem Details with `errors` |
| Unexpected failure | Bug or unanticipated infrastructure failure | `Exception` | `handle_unexpected_error` | Safe `500` Problem Details |

The handlers are registered once when the application starts:

```python
app.add_exception_handler(DomainError, handle_domain_error)
app.add_exception_handler(RequestValidationError, handle_validation_error)
app.add_exception_handler(StarletteHTTPException, handle_http_exception)
app.add_exception_handler(Exception, handle_unexpected_error)
```

FastAPI selects the handler that matches the exception type. A handler
registered for a parent class also handles its subclasses. For example,
`ProjectNotFoundError` inherits from `DomainError`, so a service can raise the
specific error without a router `try`/`except` block:

```text
DatabaseProjectService raises ProjectNotFoundError
    ↓
FastAPI matches the registered DomainError handler
    ↓
handle_domain_error reads the specific error's metadata
    ↓
The client receives a 404 Problem Details response
```

`handle_http_exception` handles errors that already have HTTP meaning, such as
an authentication dependency raising `401`, an authorization dependency
raising `403`, or FastAPI reporting an unmatched path as `404`.

`handle_validation_error` handles FastAPI's `RequestValidationError`. This is
the error FastAPI raises after Pydantic cannot validate an incoming request.
For example, a required JSON field may be missing, a name may be blank or too
long, or a path parameter expected to be an integer may contain text.

## Represent every client-visible failure with Problem Details

Each handler calls the shared `problem_response()` function. It creates an RFC
9457 response with the `application/problem+json` media type. Each response
includes a stable problem type, a short title, the HTTP status, an
occurrence-specific detail, and the request path (`instance`). Validation
responses also include an `errors` array with field-level information.

```json
{
  "type": "https://project-task-api.local/problems/project-not-found",
  "title": "Project not found",
  "status": 404,
  "detail": "The requested project does not exist.",
  "instance": "/api/v1/projects/42"
}
```

The service-layer errors remain independent of FastAPI. `DomainError` carries
the problem type, title, status code, and safe detail, while the HTTP handler
creates the HTTP response. This separation lets a service describe its
business outcome without importing FastAPI.

Unexpected failures receive a generic `500` response. The client learns that
the request failed, but does not receive a stack trace, database connection
string, or other internal implementation detail.

The same response metadata is included in OpenAPI so clients can inspect the
expected error format in Swagger UI, ReDoc, or `/openapi.json`.

## Evolve paths with a versioned API

### Choose a versioning strategy deliberately

An API version identifies a client-visible contract. Versioning is useful when
a change would otherwise break existing clients, such as removing or renaming a
field, changing a field's meaning, or changing an endpoint's behavior.

Several approaches are common:

| Strategy | Example | Strength | Trade-off |
| --- | --- | --- | --- |
| URI versioning | `/api/v1/projects` | Visible, easy to discover, and straightforward to route and document | The URL changes for each major version |
| Query-parameter versioning | `/projects?version=2` | Easy to try from a browser or API client | Can make a contract version look like an optional filter |
| Header versioning | `X-API-Version: 2` | Keeps resource URLs stable | Less visible and harder to try or discover |
| Media-type versioning | `Accept: application/vnd.example.v2+json` | Can negotiate a representation through standard HTTP headers | More complex for clients, documentation, and tooling |

This project uses **URI versioning**. The version is clear in the URL,
appears directly in OpenAPI, and makes the migration destination easy to see:
`/api/v1/projects`.

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

### Add migration headers after the route creates its response

`app.middleware("http")(add_legacy_api_headers)` registers middleware that
runs for every HTTP request. The middleware needs the route's response before
it can add `Deprecation`, `Sunset`, and `Link` headers, so it first continues
the request through the rest of the application:

```python
response = await call_next(request)
```

The request and response flow is:

```text
Request arrives
    ↓
add_legacy_api_headers starts
    ↓
await call_next(request)
    ↓
Other middleware, route matching, dependencies, and the route handler run
    ↓
A Response is produced
    ↓
The middleware resumes, adds legacy migration headers when needed,
and returns the Response to the client
```

`call_next(request)` is awaitable because the remaining request processing may
need to wait. For example, it may reach an asynchronous route, await I/O, or
run a synchronous route in FastAPI's threadpool. `await` pauses this
middleware until the response is ready, then the quick synchronous work below
it can inspect the path and modify the response headers.

### Complete the deprecation lifecycle

- Monitor requests to deprecated paths so the team can see whether clients
  have migrated.
- Give clients a clear migration guide and time to move to the versioned paths.
- After usage has stopped and the announced sunset date has passed, remove the
  deprecated routes and their migration headers.
