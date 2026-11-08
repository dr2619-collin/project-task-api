# Module 10 — Evolve Public APIs Safely

Public APIs are dependencies for other people’s software. Error behavior and
endpoint changes should therefore be designed as deliberately as successful
responses. These principles apply across programming languages, frameworks,
and API implementations.

## Make errors part of the public contract

Clients need predictable information when a request cannot be completed. Use
meaningful HTTP status codes and a consistent, documented error structure so
clients can handle failures without depending on framework-specific messages.

- Keep machine-readable identifiers and status information stable.
- Make human-readable details useful to the caller, but do not expose internal
  implementation or sensitive information.
- Document and test error responses alongside successful responses.
- Avoid requiring clients to parse prose to determine what kind of failure
  occurred.

An established format such as RFC 9457 Problem Details can provide a common
structure rather than inventing a new envelope for every API.

## Separate application outcomes from transport responses

An application rule should report what happened in terms of the application,
not how one particular protocol represents it. Keep business failures
independent of HTTP response classes, then translate them at the transport
boundary.

This lets an HTTP API map an outcome to a status code and response body while a
command-line tool, message consumer, or another transport can handle the same
outcome in its own way. It also keeps protocol details from spreading into
business logic.

## Centralize shared error policy

When many operations need the same error format and mapping rules, define that
policy in one place. Central handling reduces repeated translation code and
helps keep responses consistent as the API evolves. Keep operation-specific
business decisions in the application layer; centralization should unify how
outcomes are presented, not move those decisions out of their proper layer.

## Preserve compatibility when changing an API

Existing clients may depend on paths, request and response fields, status
codes, and error meanings. Prefer changes that preserve those expectations.
When a change is incompatible, provide an explicit migration path—often a new
API version—rather than silently changing what an existing endpoint means.

If old and new versions coexist, make clear which version clients should use
and keep their behavior intentional. Reusing the same implementation where
possible avoids maintaining duplicate business behavior for each version.

## Deprecate with a clear migration path

Deprecation is a transition, not an immediate removal. Tell clients that an
operation is deprecated, identify its replacement, and communicate a removal
timeline when one is known. Keep the old behavior available during the
announced transition period, then remove it deliberately after the migration
window.

## Keep documentation and behavior aligned

Versioning, deprecation, and error formats are promises to API consumers. Keep
the published API description, actual responses, and compatibility tests in
sync. Review changes from a client’s perspective: what continues to work, what
changes, and what must the client do next?

