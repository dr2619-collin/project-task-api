# Module 02 — Clear, Maintainable Resource APIs

Module 02 grows the single-file API into Project and Task CRUD endpoints. The structure introduces a few practices that help clients use the API predictably and help developers extend it without duplicating rules.

## Design APIs around resources

Resource-oriented API design models meaningful application data as resources and uses consistent URLs and HTTP methods to work with them. In this project, Projects and Tasks have collection and item URLs, and standard `GET`, `POST`, `PUT`, and `DELETE` operations.

The nested `GET /projects/{project_id}/tasks` URL expresses the relationship between a Project and its Tasks. Consistent names, URLs, methods, and status codes help a client predict how an unfamiliar endpoint behaves.

## Organize code so intent is clear

The Project and Task endpoints live in separate router modules, while [`app/storage.py`](../../app/storage.py) owns the shared temporary data. This separation keeps route responsibilities from becoming one large, mixed file.

**DRY — Don't Repeat Yourself** means that one rule or piece of knowledge should have one clear source of truth. The lookup helpers apply DRY: `find_project()` and `find_task()` centralize how a resource is located and how a missing resource is reported. The Task router reuses `find_project()` instead of recreating its own Project lookup.

Types can communicate domain intent as well. [`app/storage.py`](../../app/storage.py) names the dictionary shapes `Project` and `Task` with `TypeAlias`, so route signatures say `list[Project]` instead of repeating a complex dictionary type. These aliases improve readability and static checking; Module 03 later adds runtime schema validation.

## Protect domain relationships

An invariant is a condition that must remain true for application data to be valid. Module 02 protects the Project–Task relationship:

- Creating or replacing a Task verifies that its Project exists.
- Deleting a Project returns `409 Conflict` when Tasks still reference it, preventing orphaned Tasks.

These checks protect valid application state. Module 03 separately validates the shape of incoming API data, and later database constraints provide another layer of protection.
