"""FastAPI dependencies that authenticate Bearer tokens and enforce roles."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.users import AuthenticatedUser, Role, get_user_for_token

# auto_error=False lets this module return one clear 401 response for missing,
# malformed, or unknown credentials instead of relying on framework defaults.
# FastAPI also uses this scheme to add HTTP Bearer security to OpenAPI and to
# show Swagger UI's Authorize control.
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuthentication")
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


# Reuse these descriptions in router decorators so API documentation states the
# same security outcomes that the dependencies produce at runtime.
UNAUTHORIZED_RESPONSE = {
    "description": "Missing or invalid Bearer token",
    "headers": {
        "WWW-Authenticate": {
            "description": "Authentication scheme required by this endpoint.",
            "schema": {"type": "string"},
        }
    },
}
FORBIDDEN_RESPONSE = {"description": "Administrator role required"}
AUTHENTICATED_RESPONSES = {401: UNAUTHORIZED_RESPONSE}
ADMIN_RESPONSES = {401: UNAUTHORIZED_RESPONSE, 403: FORBIDDEN_RESPONSE}


def unauthenticated() -> HTTPException:
    """Build the standard response for absent or invalid credentials."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(credentials: BearerCredentials) -> AuthenticatedUser:
    """Authenticate a recognized Bearer token and return its demo user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthenticated()

    user = get_user_for_token(credentials.credentials)
    if user is None:
        raise unauthenticated()
    return user


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> AuthenticatedUser:
    """Allow only an authenticated administrator to continue to a write route."""
    if current_user.role is not Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )
    return current_user


AdminUser = Annotated[AuthenticatedUser, Depends(require_admin)]
