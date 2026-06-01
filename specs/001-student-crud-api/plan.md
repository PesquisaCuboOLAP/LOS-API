# Implementation Plan: Student CRUD API

**Branch**: `[001-student-crud-api]` | **Date**: 2026-06-01 | **Spec**: `/specs/001-student-crud-api/spec.md`

**Input**: Feature specification from `/specs/001-student-crud-api/spec.md`

## Summary

Bring the existing FastAPI student CRUD MVP into repository-constitution compliance without changing the external API surface: preserve the current `/students` endpoints and Docker Compose workflow, introduce a service layer and repository abstraction behind the router, keep PostgreSQL as the persistence backend, and add the first pytest suite covering CRUD success paths plus invalid-input and not-found cases.

## Technical Context

**Language/Version**: Python 3.12 (container runtime from `Dockerfile`)

**Primary Dependencies**: FastAPI 0.115.12, SQLAlchemy 2.0.41, Pydantic v2, psycopg2-binary 2.9.10, Uvicorn, pytest to be added during implementation

**Storage**: PostgreSQL 16 via Docker Compose service `db`, accessed through SQLAlchemy ORM; current startup bootstraps schema with `Base.metadata.create_all`

**Testing**: New pytest suite required; use FastAPI test client plus database fixtures for unit, integration, and contract coverage because no tests exist yet

**Target Platform**: Containerized Linux service via Docker Compose for local development, with macOS/Linux developer hosts

**Project Type**: Single-project backend web service

**Performance Goals**: Correctness and persistence are primary; local CRUD requests should remain lightweight and comfortably sub-200 ms p95 under normal developer usage once the container stack is warm

**Constraints**: Preserve existing endpoint paths and Docker service names `api` and `db`; keep OpenAPI docs available; follow type hints, Pydantic validation, service layer, repository pattern, and dependency injection requirements; do not introduce unrelated migration tooling in this feature

**Scale/Scope**: One resource (`Student`) with five REST endpoints, one SQLAlchemy model, one router, and a new initial automated test suite

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-Phase 0 Assessment**

- `Type hints required`: PASS. Current code is typed; new service, repository, and tests must keep explicit annotations.
- `Pytest required`: FAIL in current codebase. No pytest suite or test directory exists.
- `OpenAPI documentation required`: PASS at baseline. FastAPI already exposes generated docs; implementation will add endpoint metadata so the generated schema matches the contract artifact.
- `Pydantic validation required`: PASS at baseline. `StudentCreate` and `StudentUpdate` already validate required names; implementation will tighten blank-name handling to reject whitespace-only values.
- `Service layer`: FAIL in current codebase. Router functions currently contain database orchestration directly.
- `Repository pattern`: FAIL in current codebase. Router functions currently query the SQLAlchemy session directly.
- `Dependency injection`: PARTIAL in current codebase. FastAPI injects the DB session, but service and repository providers do not exist yet.

**Gate Decision**

Planning may proceed because the identified failures are the explicit scope of this feature implementation. No constitution exception is required if Phase 1 design introduces:

- `StudentRepository` for persistence access
- `StudentService` for CRUD orchestration and error semantics
- DI providers wiring router -> service -> repository -> session
- pytest coverage for unit, integration, and contract scopes

**Post-Phase 1 Re-Check**

- PASS. The design artifacts below close every outstanding constitution gap without requiring a waiver.

## Project Structure

### Documentation (this feature)

```text
specs/001-student-crud-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── student-crud.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── database.py
├── main.py
├── models.py
├── schemas.py
├── routers/
│   └── students.py
├── repositories/
│   └── student_repository.py      # planned
├── services/
│   └── student_service.py         # planned
└── dependencies.py                # planned DI helpers

tests/
├── conftest.py                    # planned shared fixtures
├── contract/
│   └── test_students_api.py       # planned API contract checks
├── integration/
│   └── test_student_persistence.py # planned DB-backed CRUD flow tests
└── unit/
    └── test_student_service.py    # planned service behavior tests

specs/
└── 001-student-crud-api/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── contracts/
```

**Structure Decision**: Keep the existing single FastAPI service layout under `app/` and extend it with `repositories/`, `services/`, and centralized dependency providers. Add a new top-level `tests/` tree split by unit, integration, and contract concerns so pytest coverage maps cleanly to the constitution and the spec's independent user stories.

## Implementation Phases

### Phase 0: Research

- Confirm the layering approach that best fits the existing sync FastAPI + SQLAlchemy stack.
- Define the first pytest strategy that verifies the current contract without overbuilding test infrastructure.
- Decide how design-time API contracts should mirror FastAPI's generated OpenAPI output.

### Phase 1: Design

- Model the `Student` entity plus request, response, and error payload rules.
- Specify repository and service responsibilities, especially ownership of not-found behavior and validation boundaries.
- Produce the OpenAPI contract artifact for `/students` endpoints.
- Document a quickstart that covers current Docker execution and target post-implementation validation commands.

### Phase 2: Implementation Preview

- Refactor router handlers to depend on a `StudentService` rather than `Session` directly.
- Add repository methods for create, list, fetch, update, and delete using SQLAlchemy 2.x patterns.
- Add pytest dependencies and fixtures, then implement unit, integration, and contract tests.
- Preserve the current generated OpenAPI docs and align endpoint metadata with the contract file.

## Risks And Mitigations

- `Current schema bootstrap uses create_all on startup`: acceptable for this MVP, but tests must control schema setup explicitly to avoid hidden state across runs.
- `No existing test harness`: keep the first suite small and deterministic, with shared fixtures and isolated database state per test.
- `Router currently owns DB logic`: move behavior in thin slices to reduce regression risk while preserving endpoint signatures and status codes.

## Complexity Tracking

No constitution exceptions or extra complexity waivers are required for this feature plan.
