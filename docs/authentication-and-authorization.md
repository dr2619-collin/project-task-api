# Authentication and Authorization

Module 08 protects the Project and Task resources with two simple Bearer tokens. This is a focused course demonstration, not a production identity system.

## Two related decisions

| Question | Security concept | This application answers it by |
|---|---|---|
| Who sent this request? | Authentication | Matching the submitted Bearer token to a predefined user. |
| May that user perform this action? | Authorization | Checking the user's role before the route continues. |

Authentication happens first. A request with no valid identity receives `401 Unauthorized`. Authorization happens after a valid identity exists. A valid member who attempts a write receives `403 Forbidden`.

## Course-demo policy

| Role | Token configured in `.env` | Allowed endpoints |
|---|---|---|
| Member | `DEMO_MEMBER_TOKEN` | All protected `GET` endpoints |
| Administrator | `DEMO_ADMIN_TOKEN` | All protected `GET`, `POST`, `PUT`, and `DELETE` endpoints |

`/`, `/health`, `/docs`, `/redoc`, and `/openapi.json` remain public. Both token values in `.env.example` are demonstration values, not real secrets.

## Send a Bearer token

A client sends the token in the HTTP `Authorization` header:

```text
Authorization: Bearer member-demo-token
```

For example, a member can list Projects:

```bash
curl http://localhost:8000/projects \
  -H "Authorization: Bearer member-demo-token"
```

An administrator can create a Project:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer admin-demo-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Project","description":"Created by an administrator."}'
```

Swagger UI also reads the Bearer security scheme from OpenAPI. In `http://localhost:8000/docs`, select **Authorize** and enter one of the tokens.

## Request flow and dependency injection

The application handles a protected read request such as:

```text
GET /projects
Authorization: Bearer member-demo-token
```

with this route declaration:

```python
@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="Return every project currently stored by the application.",
    responses=AUTHENTICATED_RESPONSES,
)
def list_projects(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[Project]:
    """Return Projects after FastAPI authenticates the requesting user."""
    return ProjectService(session).list_projects()
```

`current_user` and `session` are not URL or JSON-body values sent by the client. FastAPI creates and injects them before calling `list_projects()`.

### Parameter aliases

```python
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_db)]
```

Each alias contains a value type (`AuthenticatedUser` or SQLAlchemy `Session`) and a FastAPI `Depends(...)` instruction describing how to obtain that value. `Annotated` is standard Python typing syntax; FastAPI reads the `Depends(...)` metadata and performs dependency injection.

### Extracting Bearer credentials

`get_current_user()` has another dependency:

```python
def get_current_user(credentials: BearerCredentials) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthenticated()

    user = get_user_for_token(credentials.credentials)
    if user is None:
        raise unauthenticated()
    return user
```

`BearerCredentials` tells FastAPI to run `HTTPBearer` first:

```python
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuthentication",
)

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]
```

`HTTPBearer` reads the HTTP `Authorization` header. Given:

```text
Authorization: Bearer member-demo-token
```

it returns an object equivalent to:

```python
HTTPAuthorizationCredentials(
    scheme="Bearer",
    credentials="member-demo-token",
)
```

FastAPI supplies that object as the `credentials` argument of `get_current_user()`. `auto_error=False` means a missing or malformed credential becomes `None`, allowing the application to return its consistent `401 Unauthorized` response with `WWW-Authenticate: Bearer`. `scheme_name` supplies the security-scheme name in OpenAPI and Swagger UI; it does not change the HTTP header format.

### One complete `GET /projects` request

```text
1. Client sends GET /projects with Authorization: Bearer member-demo-token.

2. FastAPI selects list_projects().

3. FastAPI resolves current_user: CurrentUser.
   CurrentUser requires get_current_user().

4. get_current_user() requires credentials: BearerCredentials.
   BearerCredentials requires bearer_scheme.

5. HTTPBearer reads the Authorization header and returns credentials.

6. get_current_user() maps the token to:
   AuthenticatedUser(username="member", role=Role.MEMBER).

7. FastAPI supplies this object as current_user.

8. FastAPI resolves session: DatabaseSession.
   get_db() creates and yields a SQLAlchemy Session.

9. FastAPI calls list_projects(current_user=<AuthenticatedUser>, session=<Session>).

10. The route calls ProjectService(session).list_projects().
    The service and repository query PostgreSQL.

11. FastAPI validates and serializes the result as list[ProjectResponse],
    then sends 200 OK with JSON.

12. FastAPI resumes get_db() so the database Session can close.
```

The route function does not manually call `bearer_scheme`, `get_current_user`, or `get_db`. FastAPI calls them because it recognizes their nested `Depends(...)` declarations.

`app/auth/users.py` holds the intentionally small identity model and reads the token values from environment variables. It reads the environment at request time, which also lets tests safely override a token when needed.

## HTTP outcomes

| Situation | Status | Response behavior |
|---|---:|---|
| No token or unknown token | `401 Unauthorized` | Returns a JSON `detail` and `WWW-Authenticate: Bearer`. |
| Valid member uses a write endpoint | `403 Forbidden` | Returns a JSON `detail`; the request does not reach the service layer. |
| Valid token and allowed action | Normal endpoint status | For example, `200`, `201`, or `204`. |

The `HTTPBearer` dependency also adds the Bearer security scheme to `/openapi.json`. Route decorators document the relevant `401` and `403` responses.

### Write routes add authorization

Write routes use a nested dependency:

```python
AdminUser = Annotated[AuthenticatedUser, Depends(require_admin)]

def require_admin(current_user: CurrentUser) -> AuthenticatedUser:
    if current_user.role is not Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )
    return current_user
```

FastAPI first resolves `CurrentUser`, then passes that resulting `AuthenticatedUser` as the `current_user` argument to `require_admin()`. This creates the write-route chain:

```text
Authorization header
  -> HTTPBearer extracts credentials
  -> get_current_user authenticates the token
  -> require_admin authorizes the user's role
  -> write route runs only for an administrator
```

## Tests

The test suite covers the same separation of responsibilities:

| Test location | What it verifies |
|---|---|
| `tests/unit/auth/test_dependencies.py` | Token mapping, `401` handling, and the administrator role check without FastAPI or PostgreSQL. |
| `tests/integration/test_authentication_authorization_api.py` | Public endpoints, missing/invalid tokens, member reads, member write rejection, and an administrator CRUD workflow. |
| `tests/conformance/test_authentication_authorization_contract.py` | OpenAPI publishes the Bearer scheme, security requirements, and documented security outcomes. |

Existing Project and Task API tests use the shared `admin_client` fixture because their purpose is to verify normal CRUD behavior after authorization succeeds. The ordinary `client` fixture stays unauthenticated for tests that need to verify `401` behavior.

## OAuth2 and JWT: related, but not implemented here

OAuth2 is an authorization framework. In a production system, an identity provider may authenticate a user and issue an access token that this API validates. JWT is a signed token format often used for such access tokens; it is not encrypted by default, and possessing a JWT is not itself an authorization policy.

This module uses static tokens instead so the class can clearly see FastAPI dependency injection, a Bearer header, `401` versus `403`, and role-based access control. A later production design would use securely managed secrets, real identities, a token issuer or identity provider, expiration, rotation or revocation, and careful audit logging.

Never log raw `Authorization` headers or token values. Even though this module's values are safe demonstration credentials, real Bearer tokens must be treated like passwords.
