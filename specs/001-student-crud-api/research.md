# Research: Student CRUD API

## Decision 1: Use a thin router -> service -> repository flow

- Decision: Introduce `StudentService` and `StudentRepository` while keeping FastAPI route functions thin and preserving the existing endpoint paths and response codes.
- Rationale: The constitution explicitly requires a service layer, repository pattern, and dependency injection. The current router already defines the right HTTP surface, so the least disruptive change is to move CRUD orchestration and persistence access behind those existing handlers.
- Alternatives considered: Keep direct session access in the router. Rejected because it would leave the codebase out of constitutional compliance and make unit testing harder.

## Decision 2: Keep FastAPI dependency injection and extend it to service and repository providers

- Decision: Add dependency provider functions that construct `StudentRepository` from the SQLAlchemy session and `StudentService` from the repository.
- Rationale: The repo already uses `Depends(get_db)` successfully. Extending the same pattern keeps the architecture idiomatic for FastAPI and avoids introducing a separate container framework.
- Alternatives considered: Instantiate services directly inside route handlers. Rejected because it mixes wiring with request logic and weakens test isolation.

## Decision 3: Add pytest coverage in three slices instead of a single monolithic suite

- Decision: Create `tests/unit`, `tests/integration`, and `tests/contract` with shared fixtures in `tests/conftest.py`.
- Rationale: The spec asks for CRUD coverage, invalid-input coverage, and not-found coverage. Splitting tests by scope keeps feedback loops short: service behavior can be validated without HTTP overhead, while contract and persistence tests still prove the live API behavior.
- Alternatives considered: Only end-to-end API tests. Rejected because they would satisfy the minimum requirement but make it harder to pinpoint failures during the first architectural refactor.

## Decision 4: Treat whitespace-only names as invalid input

- Decision: Tighten request validation so names that are empty after trimming whitespace are rejected for create and update operations.
- Rationale: The spec explicitly calls out missing and empty names. Rejecting whitespace-only input is the most defensible interpretation of "valid student name" and avoids persisting unusable data.
- Alternatives considered: Preserve the current `min_length=1` behavior exactly. Rejected because it would accept values like `"   "`, which is inconsistent with the intent of the validation requirement.

## Decision 5: Keep `Base.metadata.create_all` for this feature and defer migration tooling

- Decision: Leave schema bootstrapping on startup in place for this feature and ensure tests create and tear down schema explicitly.
- Rationale: The repo already relies on `create_all`, and the feature scope is limited to one existing table plus architectural/test hardening. Introducing Alembic would enlarge the change set beyond the stated requirement.
- Alternatives considered: Add Alembic migrations now. Rejected because it is not required by the constitution or the feature spec and would add unrelated operational complexity.

## Decision 6: Document the API contract as OpenAPI YAML under `contracts/`

- Decision: Add a design-time OpenAPI artifact for the student CRUD endpoints and treat FastAPI's generated schema as the runtime source of truth to match.
- Rationale: The repo already exposes Swagger/OpenAPI output automatically, and the planning workflow expects a contract artifact under `contracts/`. OpenAPI YAML is the closest match to the existing implementation style.
- Alternatives considered: Use markdown-only endpoint notes. Rejected because they are harder to validate against generated FastAPI docs and less precise for response schemas/status codes.