"""Unit tests for the Module 08 Bearer-token authentication dependencies."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import get_current_user, require_admin
from app.auth.users import AuthenticatedUser, Role, demo_token_for


# AUTHENTICATION
# These tests call the dependency functions directly, so they do not start
# FastAPI, Docker, or PostgreSQL. They isolate token-to-user mapping and the
# HTTP errors returned for a missing or invalid credential.


@pytest.mark.parametrize(
    ("role", "username"),
    [(Role.MEMBER, "member"), (Role.ADMIN, "admin")],
)
def test_valid_demo_token_authenticates_its_predefined_user(
    role: Role,
    username: str,
) -> None:
    """Each configured course-demo token resolves to its fixed user and role."""
    user = get_current_user(bearer_credentials(demo_token_for(role)))

    assert user == AuthenticatedUser(username=username, role=role)


@pytest.mark.parametrize(
    "credentials",
    [
        None,
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-demo-token"),
        HTTPAuthorizationCredentials(scheme="Basic", credentials="token"),
    ],
    ids=["missing", "unknown-token", "wrong-scheme"],
)
def test_missing_or_invalid_credentials_return_bearer_401(
    credentials: HTTPAuthorizationCredentials | None,
) -> None:
    """Unauthenticated requests return 401 and advertise the Bearer scheme."""
    with pytest.raises(HTTPException) as error:
        get_current_user(credentials)

    assert error.value.status_code == 401
    assert error.value.detail == "Missing or invalid Bearer token"
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


# AUTHORIZATION
# Authentication establishes the user. Authorization then decides whether the
# established role may perform an administrator-only operation.


def test_member_cannot_pass_the_administrator_requirement() -> None:
    """A valid member identity receives 403 when an admin role is required."""
    member = AuthenticatedUser(username="member", role=Role.MEMBER)

    with pytest.raises(HTTPException) as error:
        require_admin(member)

    assert error.value.status_code == 403
    assert error.value.detail == "Administrator role required"


def test_administrator_passes_the_administrator_requirement() -> None:
    """The dependency returns the authenticated administrator to the route."""
    admin = AuthenticatedUser(username="admin", role=Role.ADMIN)

    assert require_admin(admin) is admin


# HELPERS


def bearer_credentials(
    token: str,
    scheme: str = "Bearer",
) -> HTTPAuthorizationCredentials:
    """Build the credentials object that FastAPI's HTTPBearer normally yields."""
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
