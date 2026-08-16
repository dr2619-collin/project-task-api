"""Predefined demonstration users and roles for Module 08.

This module intentionally does not model a production user store. It maps two
environment-configured course-demo tokens to fixed identities and roles so the
authentication and authorization request flow remains easy to inspect.
"""

import os
from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """Roles supported by the simple course-demo permission policy."""

    MEMBER = "member"
    ADMIN = "admin"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represent the identity and role established by a valid Bearer token."""

    username: str
    role: Role


# These defaults make the classroom demo and automated tests runnable without
# a local .env file. A real deployment supplies different values through the
# environment and never commits those values to source control.
DEFAULT_MEMBER_TOKEN = "member-demo-token"
DEFAULT_ADMIN_TOKEN = "admin-demo-token"


def demo_token_for(role: Role) -> str:
    """Return the configured course-demo token for one role.

    Read the environment when a request is authenticated rather than at module
    import time. This keeps configuration visible and makes isolated tests able
    to override a token without recreating the Python process.
    """
    if role is Role.MEMBER:
        return os.getenv("DEMO_MEMBER_TOKEN", DEFAULT_MEMBER_TOKEN)
    return os.getenv("DEMO_ADMIN_TOKEN", DEFAULT_ADMIN_TOKEN)


def get_user_for_token(token: str) -> AuthenticatedUser | None:
    """Map one configured demo token to its predefined user and role."""
    member_token = demo_token_for(Role.MEMBER)
    admin_token = demo_token_for(Role.ADMIN)

    # Empty environment values must not accidentally authenticate an empty
    # credential. An empty string is therefore treated as unconfigured.
    if member_token and token == member_token:
        return AuthenticatedUser(username="member", role=Role.MEMBER)
    if admin_token and token == admin_token:
        return AuthenticatedUser(username="admin", role=Role.ADMIN)
    return None
