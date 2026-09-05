# Module 01 — Project Foundations

Module 01 establishes two habits that support every later feature: manage dependencies deliberately and keep the initial design proportionate to the current requirements.

## Dependency management

Dependency management is the practice of declaring, resolving, installing, and updating the external software components an application needs. It involves both a tool that manages the work and project files that describe the result.

In this Python project, `uv` is the dependency-management and environment-management tool. It fills a role similar to Maven or Gradle in a Java project. `pyproject.toml` is the project manifest, similar in purpose to Maven's `pom.xml` or a Gradle build file: it declares project metadata and direct dependencies. `uv.lock` records the exact dependency versions that `uv` resolved.

Module 01 uses:

- `uv` to resolve and install dependencies, manage the project environment, and run commands within it.
- [`pyproject.toml`](../../pyproject.toml) to declare project metadata, the supported Python version, and direct dependencies such as FastAPI and Uvicorn.
- [`uv.lock`](../../uv.lock) to record the complete resolved dependency graph and exact package versions.

Running `uv sync` makes the local environment match the manifest and lock file. Running a command through `uv run` uses that managed project environment rather than assuming the correct packages are installed globally.

## Use version control for software projects

Version control records the history of a project so changes can be reviewed, shared, compared, and recovered. A source-control repository is a normal foundation for software work, not an optional step added only after a project becomes large.

This course repository uses a branch for each module, allowing each stage of the API to build on the previous one while preserving the earlier implementation for comparison. In a team, a shared remote repository also provides a common place to collaborate and review changes.

Make small, coherent commits with messages that explain the purpose of the change. Use branches to isolate work, and review the changed files before committing. Version control does not replace backups or testing, but it makes experimentation and correction much safer.

### Keep local and generated files out of version control

Use a [`.gitignore`](../../.gitignore) file to exclude files that do not belong in the shared source of truth, such as local environments, editor settings, generated caches, and local configuration files. This keeps commits focused on the code and documentation that other developers need.

## Write a README for the next developer

A README is the project’s starting point for a new developer. It should explain what the project does, how to set it up and run it, and the most useful next steps for exploring or contributing to it.

Module 01's [`README.md`](../../README.md) describes the Project and Task API, identifies the module scope, provides setup and run commands, and shows how to try the endpoints. As the application grows, the README should stay accurate and point readers to deeper documentation rather than attempting to contain every detail itself.

Good README content is specific enough that a new developer can start the project without guessing, but brief enough that it remains maintained. Treat it as part of the software product, not as an afterthought.

## KISS — Keep It Simple

KISS means Keep It Simple. Traditionally, the final word is “Stupid”; the principle is about avoiding unnecessary complexity, not about the people building the software. Prefer the least complicated design that clearly satisfies the current requirements.

Module 01 needs to start a FastAPI application, introduce the API, and report its health. Those behaviors fit clearly in [`app/main.py`](../../app/main.py). The module does not add routers, services, repositories, database models, or dependency injection before those structures solve a current problem.

KISS does not mean omitting required behavior or ignoring quality. A simple solution can still use clear names, types, documentation, and error handling.
