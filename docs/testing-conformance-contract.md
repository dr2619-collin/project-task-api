# Conformance and Contract Testing

Module 07 extends the Module 06 test suite with tests for the API's public agreement: its OpenAPI document and the HTTP behavior clients receive.

For the Module 06 unit-test, integration-test, fixture, and Testcontainers foundation, see [Unit and Integration Testing](testing-unit-integration.md).

## Testing purpose and approach

| Testing purpose | Module 07 approach |
|---|---|
| OpenAPI document validity | `openapi-spec-validator` validates the complete generated document. |
| Contract expectations | Ordinary pytest and `TestClient` assertions check required paths, schemas, status codes, and representative responses. |
| Conformance testing | The contract assertions plus Schemathesis confirm that the API follows its published OpenAPI behavior. |
| Schema-driven testing / light fuzzing | Schemathesis generates requests from OpenAPI and validates the responses. |
| Negative testing | Ordinary pytest and `TestClient` send invalid requests and check expected `422`, `404`, or `409` responses. |

Negative tests could technically be integration tests in Module 06. In Module 07, their teaching purpose is to show the client-visible error behavior that belongs to the API contract.

## The question each module answers

| Module 06 | Module 07 |
|---|---|
| Does this Python behavior or normal API workflow work? | Can an API client rely on the published interface? |
| Unit and integration tests | Conformance, contract, and negative tests |
| Expected behavior is written directly in a test | Expected behavior is also checked against `/openapi.json` |

The **OpenAPI contract** describes the API's paths, HTTP methods, request bodies, response bodies, types, required fields, and status codes. A client such as a front end, mobile app, or another service depends on those details.

**Conformance testing** checks whether the API implementation follows that declared contract. **Contract testing** emphasizes the relationship between the provider and the consumers that depend on it.

## Module 07 test layout

```text
tests/
├── conftest.py
├── conformance/
│   ├── test_authentication_authorization_contract.py
│   ├── test_negative_requests.py
│   └── test_openapi_contract.py
├── integration/
│   └── ... Module 06 tests ...
└── unit/
    └── ... Module 06 tests ...
```

The conformance tests reuse the Module 06 `client` fixture. Tests that need normal protected resource behavior use the Module 08 `admin_client` fixture, which adds the demonstration administrator's Bearer header:

```text
TestClient -> FastAPI router -> service -> repository -> SQLAlchemy -> PostgreSQL Testcontainer
```

They are full API tests, not router-only unit tests. Every test receives an empty temporary PostgreSQL database, and no test uses the local `project_task` development database.

## Validate the OpenAPI document

FastAPI generates `/openapi.json` from route decorators, type hints, Pydantic schemas, status-code settings, and response models.

`openapi-spec-validator` validates the complete generated document against the OpenAPI specification. It answers: “Is this a structurally valid OpenAPI document?”

```python
response = client.get("/openapi.json")
validate(response.json())
```

The test also contains approved expectations for this API: its public paths and methods, response statuses, request/response component schemas, and the response-model references used after creating a Project or Task.

This extra step is important for a code-first framework. If code changes, FastAPI can generate a new valid OpenAPI document automatically. Structural validation alone would not tell us whether a required path, field, or status code was unintentionally removed. The approved expectations represent what the API's consumers rely on.

`openapi-schema-validator` has a different job: it validates a data value against one individual OpenAPI schema. Module 07 uses `openapi-spec-validator` for the complete contract document.

## Why use Schemathesis instead of `openapi-schema-validator` here?

`openapi-schema-validator` is a lower-level library. To validate a response with it, a test would need to send the request, locate the correct response schema in `/openapi.json`, resolve references such as `#/components/schemas/ProjectResponse`, and then pass both the JSON response and the resolved schema to the validator.

Schemathesis automates that API-level workflow. It reads the OpenAPI document, generates requests from its operations and constraints, sends those requests to FastAPI, and validates the resulting status code and response body against the documented operation.

```text
OpenAPI contract
  -> generated request cases
  -> real API response
  -> automatic contract validation
```

This makes Schemathesis a better fit for Module 07's schema-driven testing demonstration. It does not replace the readable pytest tests for known business rules such as `404 Not Found` for a missing resource or `409 Conflict` when a Project still has Tasks.

Use `openapi-schema-validator` directly when a program needs custom validation of one known JSON value against one known OpenAPI schema outside a full API test. It is installed indirectly because `openapi-spec-validator` depends on it, but this project does not import it directly.

## Conformance of actual responses

The targeted tests send real requests and verify consumer-visible behavior:

- Creating a Project returns `201 Created` and the documented `ProjectResponse` shape.
- Requesting a missing Project returns `404 Not Found`.
- Deleting a Project with related Tasks returns `409 Conflict`.

The tests assert stable contract details—status codes and JSON shapes—not the exact human-readable `detail` text unless that text is intentionally documented as part of the contract.

Module 08 also adds a focused security-contract test. It confirms that OpenAPI publishes the reusable HTTP Bearer scheme, marks representative resource operations as protected, and documents their `401` and `403` outcomes.

## Negative testing

A **negative test** intentionally sends invalid or disallowed input. It passes when the API rejects the request safely and predictably.

Module 07 checks these categories:

| Invalid or disallowed request | Expected status | Who enforces it? |
|---|---:|---|
| Missing or unknown Project JSON field | `422` | FastAPI and Pydantic |
| Blank or overlong Project name | `422` | Pydantic field constraints |
| Non-integer Project or Task path ID | `422` | FastAPI typed-path validation |
| Missing Project or Task | `404` | Application service and router |
| Task references nonexistent Project | `404` | Application relationship rule |
| Delete Project that has Tasks | `409` | Application business rule |

`422 Unprocessable Content` means FastAPI validated a request against a typed parameter or Pydantic model and rejected it before the route handler completed. `404` and `409` here are business outcomes deliberately translated by our router code.

## Schema-driven testing with Schemathesis

Schemathesis reads the generated OpenAPI document and creates test cases from its declared operations, types, and constraints. It then validates actual responses against the documented operation.

The Module 07 demonstration uses only safe read-only operations:

```text
GET /health
GET /projects
GET /tasks
```

The test loads the FastAPI ASGI application directly through a pytest fixture. It does not start Uvicorn, open port 8000, or send requests to a local development server.

### How Schemathesis connects to pytest

The connection between the fixture and the generated test is intentionally deferred:

```python
@pytest.fixture
def openapi_schema(admin_client: TestClient) -> Any:
    from app.main import app

    return schemathesis.openapi.from_asgi("/openapi.json", app)


schema = schemathesis.pytest.from_fixture("openapi_schema").include(
    method="GET",
    path_regex=r"^/(health|projects|tasks)$",
)
```

`openapi_schema` is an ordinary pytest fixture. It requests `admin_client`, which ensures the Testcontainer database and in-process FastAPI application are ready before FastAPI is imported and the OpenAPI document is loaded. The administrator header lets the generated protected `GET` requests reach their successful response behavior.

`schemathesis.pytest.from_fixture("openapi_schema")` creates a **lazy schema**. It means, “when a generated test runs, ask pytest for the fixture named `openapi_schema`.” It does not create the real schema while pytest is collecting test files. This matters because importing the application during test collection would happen before the test fixture sets `DATABASE_URL` to the temporary database.

The lazy schema is then used as a decorator:

```python
@schema.parametrize()
def test_generated_read_only_responses_conform_to_openapi(
    case: Any,
    admin_client: TestClient,
) -> None:
    case.call_and_validate(session=admin_client)
```

`@schema.parametrize()` transforms one Python test function into one generated subtest for each selected OpenAPI operation. In this project, it produces `GET /health`, `GET /projects`, and `GET /tasks`.

`case` is supplied by Schemathesis, not by pytest. It represents one generated request and its documented OpenAPI operation. `client` is the ordinary pytest fixture. The runtime flow is:

```text
Schemathesis-generated subtest
  -> pytest creates admin_client
      -> Testcontainers starts PostgreSQL
      -> TestClient starts FastAPI in-process
  -> Schemathesis resolves openapi_schema
      -> reads /openapi.json from FastAPI
  -> Schemathesis provides one case
  -> case.call_and_validate(session=admin_client)
      -> sends the request through TestClient
      -> validates the status, headers, and response body against OpenAPI
```

Schemathesis is a complement to readable, intentional tests. It can explore additional cases, but it does not replace a clear test that documents a particular rule such as the `409` Project-with-Tasks conflict.

Write-oriented operations are intentionally excluded from this first demonstration. Generated `POST`, `PUT`, and `DELETE` requests would create or change state, which is useful later but would distract from the core Module 07 lesson.

## Run the suite

Start Docker Desktop, then run all tests from the repository root:

```bash
uv run pytest
```

To focus on the new Module 07 tests:

```bash
uv run pytest tests/conformance
```

The pytest command starts one disposable PostgreSQL Testcontainer when it first needs the API fixtures. The test database is reset around each conformance test and removed when pytest finishes.
