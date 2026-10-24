# Module 08 — Authentication and Authorization

Module 08 adds identity checks and access rules to the Project and Task API.
These security concerns affect every protected request, so they should be
designed as clear, consistent policies at the API boundary.

## Separate authentication from authorization

Authentication establishes who is making a request. Authorization decides
whether that identity may perform the requested action. Keeping these decisions
separate makes the outcomes clear:

- Return `401 Unauthorized` when the request has no valid identity.
- Return `403 Forbidden` when the identity is valid but lacks permission.

The application authenticates a Bearer token into an `AuthenticatedUser`, then
checks that user's role against the operation's access requirement. The
authentication and authorization flow is described in
[Authentication and Authorization](../authentication-and-authorization.md).

## Apply access control at the boundary

The API boundary is the right place to reject a request that is unauthenticated
or unauthorized. Protected operations should not call application services
until their access requirements are satisfied. This keeps security checks
consistent and avoids placing HTTP identity details inside business logic or
persistence code.

Security requirements should be explicit for each operation. Public operations
are intentionally public; protected operations declare the identity or role
they require. A missing security declaration should not accidentally make a
protected operation available.

## Follow least privilege

Give each role only the access it needs. In this API, members can read Projects
and Tasks, while administrators can also create, replace, and delete them.
Keeping the policy small and explicit makes it easier to review and test.

## Keep identity proof separate from application permissions

An identity provider can establish a user's identity and provide trusted claims
or permissions. The API still needs an authorization policy that decides what
those claims allow in this application. This separation lets an identity
provider or token format change without changing the meaning of application
operations such as reading a Project or creating a Task.

## Treat security outcomes as part of the API contract

Clients depend on predictable security behavior. The API should document which
operations require authentication and the expected `401` and `403` responses.
Tests should verify both sides of the policy: allowed requests succeed, and
missing identity or insufficient permission is rejected before the operation
runs.

For the production token and identity-provider context, see
[Authentication and Authorization](../authentication-and-authorization.md).
