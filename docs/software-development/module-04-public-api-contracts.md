# Module 04 — Public API Contracts

Module 04 treats the API documentation as a deliberate interface for clients. The routes, schemas, response codes, descriptions, and examples together form a contract that people and programs use to understand the application.

## APIs are public contracts

An API contract describes how a client can interact with a system: available operations, required input, returned data, and possible outcomes. A useful contract is intentional rather than an accidental by-product of implementation details.

The implementation contributes different parts of this contract:

- [`app/main.py`](../../app/main.py) gives the API a title, description, version, and resource-group descriptions.
- The Project and Task routers declare operation summaries, descriptions, success status codes, response models, and application-level error responses.
- The Project and Task schemas supply field descriptions and realistic examples.

FastAPI produces the same contract in three forms:

- Interactive Swagger UI at `/docs`
- Reference-oriented ReDoc at `/redoc`
- Machine-readable OpenAPI JSON at `/openapi.json`

Other technology stacks can use different tools, but the general practice is the same: treat the published API description as part of the interface clients rely on.

## Consistency and least surprise

Clients should not have to rediscover the rules for every endpoint. Consistency makes an unfamiliar operation easier to use correctly, including consistent:

- Resource names
- Status codes
- Input and output shapes
- Error behavior

Projects and Tasks use the same collection and item URL patterns, the same response-model approach, and parallel summaries and descriptions. The routes also document application-defined errors:

- `404 Not Found` for a missing resource
- `409 Conflict` when a Project still has Tasks

Some outcomes are supplied automatically by the framework. For example, FastAPI documents a `422` validation response because a path parameter such as `project_id: int` or a Pydantic schema has validation rules. Application-specific outcomes that occur inside helpers, such as `find_project()` raising a `404`, must be documented explicitly with the route's `responses` metadata.

## Documentation is maintained with the code

Documentation is most dependable when it lives beside the code that changes its behavior. Module 04 keeps these items near their routes and schema fields:

- Descriptions
- Examples
- Expected responses

This lets a change to an endpoint update its contract at the same time.

This does not eliminate the need for a README, tutorials, or client guides. It ensures that the API reference stays connected to executable behavior and gives those other documents a reliable source of truth.
