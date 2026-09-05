# Module 03 — Data Contracts and Validation

Module 03 replaces loose dictionaries with Pydantic schemas. The API now makes its data expectations explicit, validates external input before route logic runs, and separates values controlled by clients from values controlled by the server.

## Design by contract and boundary validation

Design by contract makes expectations at a boundary explicit: what input is valid, what output has a defined shape, and what rules must be true. Module 03 uses Pydantic models to turn those expectations into executable API contracts.

[`app/schemas/projects.py`](../../app/schemas/projects.py) and [`app/schemas/tasks.py`](../../app/schemas/tasks.py) define required fields, types, length limits, defaults, and numeric constraints. FastAPI uses these contracts to reject malformed requests before a route function runs and to describe the API in OpenAPI.

Boundary validation checks the shape of incoming data. Domain rules, such as the Project–Task invariant introduced in Module 02, remain separate from this request-shape validation.

## Separate input and output models

Client input and server output have different responsibilities. Module 03 keeps them separate so that a client cannot supply values owned by the server.

`ProjectInput` contains the editable Project fields used for both creation and full replacement, while `ProjectResponse` also includes the server-generated `id`. `TaskInput` and `TaskResponse` follow the same pattern. Route functions create response models after generating identifiers rather than accepting those identifiers from a request body.

The create and replacement inputs are intentionally the same in this module. Separate models should be added only when their rules genuinely differ—for example, if an update permits only some fields or a `PATCH` endpoint makes fields optional.

## Immutable data contracts

The shared Project and Task schema configurations use Pydantic's `frozen=True` setting. Once a request or response schema is created, it represents one fixed set of values; replacing a Project or Task creates a new response model instead of modifying the old model.

Immutable values are easier to share and reason about because one consumer cannot change what another consumer sees. This is especially useful in concurrent code, where shared mutable state can make behavior depend on timing. Immutability does not eliminate the need for clear ownership of mutable state, and it does not mean every object should be immutable. Later ORM entities remain mutable because the ORM tracks changes to them.
