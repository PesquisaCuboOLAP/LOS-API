---

description: "Implementation tasks for the Student CRUD API feature"

---

# Tasks: Student CRUD API

**Input**: Design documents from `/specs/001-student-crud-api/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/student-crud.openapi.yaml

**Tests**: Pytest coverage is required by the specification, so unit, integration, and contract tests are included for each story.

**Organization**: Tasks are grouped by user story to keep each increment independently testable while respecting shared file dependencies in the existing FastAPI app.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependency)
- **[Story]**: User story label for traceability (`[US1]`, `[US2]`, `[US3]`)
- Every task includes the exact file path to change

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the minimum shared tooling needed before test-first implementation can begin.

- [x] T001 Add pytest to `requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared scaffolding that every user story relies on.

**⚠️ CRITICAL**: No user story implementation should start until this phase is complete.

- [x] T002 Create shared database session, schema reset, and API client fixtures in `tests/conftest.py`
- [x] T003 Create the `StudentRepository` skeleton with typed CRUD method signatures in `app/repositories/student_repository.py`
- [x] T004 Create the `StudentService` skeleton with typed CRUD method signatures in `app/services/student_service.py`
- [x] T005 Add `get_student_repository` and `get_student_service` providers in `app/dependencies.py`
- [x] T006 Tighten trimmed-name validation for `StudentCreate` and `StudentUpdate` in `app/schemas.py`

**Checkpoint**: Test infrastructure, validation rules, and dependency wiring are ready for story work.

---

## Phase 3: User Story 1 - Create and list students (Priority: P1) 🎯 MVP

**Goal**: Preserve the existing POST and GET student API surface while moving create, list, and read-by-id behavior behind the new service and repository layers.

**Independent Test**: Start the app with PostgreSQL, create a student through `POST /students`, then verify `GET /students` and `GET /students/{student_id}` return the persisted record.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add create, list, get-by-id, and missing-student unit coverage in `tests/unit/test_student_service.py`
- [ ] T008 [P] [US1] Add create, list, and get-by-id persistence scenarios in `tests/integration/test_student_persistence.py`
- [ ] T009 [P] [US1] Add POST `/students`, GET `/students`, and GET `/students/{student_id}` contract coverage in `tests/contract/test_students_api.py`

### Implementation for User Story 1

- [ ] T010 [US1] Implement create, list, and get-by-id repository methods in `app/repositories/student_repository.py`
- [ ] T011 [US1] Implement create, list, and get-by-id service methods with 404 read semantics in `app/services/student_service.py`
- [ ] T012 [US1] Refactor POST `/students`, GET `/students`, and GET `/students/{student_id}` handlers to use `StudentService` in `app/routers/students.py`

**Checkpoint**: User Story 1 is independently functional and testable as the MVP.

---

## Phase 4: User Story 2 - Update student details (Priority: P2)

**Goal**: Support updating an existing student's name without changing the public API or creating missing students implicitly.

**Independent Test**: Create a student, update the name through `PUT /students/{student_id}`, then retrieve the same student and confirm the persisted name change; verify a missing id returns 404.

### Tests for User Story 2

- [ ] T013 [P] [US2] Add update success and missing-student unit coverage in `tests/unit/test_student_service.py`
- [ ] T014 [P] [US2] Add update persistence scenarios in `tests/integration/test_student_persistence.py`
- [ ] T015 [P] [US2] Add PUT `/students/{student_id}` contract coverage in `tests/contract/test_students_api.py`

### Implementation for User Story 2

- [ ] T016 [US2] Implement the update repository method in `app/repositories/student_repository.py`
- [ ] T017 [US2] Implement update service behavior without upsert semantics in `app/services/student_service.py`
- [ ] T018 [US2] Refactor PUT `/students/{student_id}` to use `StudentService` in `app/routers/students.py`

**Checkpoint**: User Stories 1 and 2 both work independently, and update behavior remains contract-compliant.

---

## Phase 5: User Story 3 - Delete students (Priority: P3)

**Goal**: Complete the CRUD surface by deleting existing students and returning a not-found response for missing ids.

**Independent Test**: Create a student, delete it through `DELETE /students/{student_id}`, then verify a follow-up read returns 404; verify deleting a missing id also returns 404.

### Tests for User Story 3

- [ ] T019 [P] [US3] Add delete success and missing-student unit coverage in `tests/unit/test_student_service.py`
- [ ] T020 [P] [US3] Add delete persistence scenarios in `tests/integration/test_student_persistence.py`
- [ ] T021 [P] [US3] Add DELETE `/students/{student_id}` contract coverage in `tests/contract/test_students_api.py`

### Implementation for User Story 3

- [ ] T022 [US3] Implement the delete repository method in `app/repositories/student_repository.py`
- [ ] T023 [US3] Implement delete service behavior and missing-student errors in `app/services/student_service.py`
- [ ] T024 [US3] Refactor DELETE `/students/{student_id}` to use `StudentService` in `app/routers/students.py`

**Checkpoint**: All three user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize developer workflow and run the documented validation path.

- [ ] T025 [P] Update pytest and layered-architecture usage notes in `README.md`
- [ ] T026 Run the documented validation flow from `specs/001-student-crud-api/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies.
- **Phase 2: Foundational** depends on Phase 1 and blocks all story work.
- **Phase 3: US1** depends on Phase 2 and delivers the MVP.
- **Phase 4: US2** depends on Phase 3 because it extends the same repository, service, router, and test files created for US1.
- **Phase 5: US3** depends on Phase 4 because it extends the same repository, service, router, and test files used by US1 and US2.
- **Phase 6: Polish** depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No story dependency after the foundational phase.
- **US2 (P2)**: Depends on US1's create and retrieval flow to supply an existing student for update scenarios.
- **US3 (P3)**: Depends on US1's create and retrieval flow and should follow US2 to avoid repeated edits in the shared implementation files.

### Within Each User Story

- Tests must be written first and fail before implementation begins.
- Repository changes come before service changes.
- Service changes come before router refactors.
- Story-specific validation completes before moving to the next priority.

### Parallel Opportunities

- `T007`, `T008`, and `T009` can run in parallel once foundational work is complete.
- `T013`, `T014`, and `T015` can run in parallel once US1 is complete.
- `T019`, `T020`, and `T021` can run in parallel once US2 is complete.
- `T025` can run in parallel with final validation once implementation is stable.

---

## Parallel Example: User Story 1

```bash
# Launch all User Story 1 test tasks together:
Task: "Add create, list, get-by-id, and missing-student unit coverage in tests/unit/test_student_service.py"
Task: "Add create, list, and get-by-id persistence scenarios in tests/integration/test_student_persistence.py"
Task: "Add POST /students, GET /students, and GET /students/{student_id} contract coverage in tests/contract/test_students_api.py"
```

## Parallel Example: User Story 2

```bash
# Launch all User Story 2 test tasks together:
Task: "Add update success and missing-student unit coverage in tests/unit/test_student_service.py"
Task: "Add update persistence scenarios in tests/integration/test_student_persistence.py"
Task: "Add PUT /students/{student_id} contract coverage in tests/contract/test_students_api.py"
```

## Parallel Example: User Story 3

```bash
# Launch all User Story 3 test tasks together:
Task: "Add delete success and missing-student unit coverage in tests/unit/test_student_service.py"
Task: "Add delete persistence scenarios in tests/integration/test_student_persistence.py"
Task: "Add DELETE /students/{student_id} contract coverage in tests/contract/test_students_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate `POST /students`, `GET /students`, and `GET /students/{student_id}` against PostgreSQL and pytest.

### Incremental Delivery

1. Finish the shared scaffolding and validation rules.
2. Deliver US1 as the first usable increment.
3. Extend the same layers for US2 update behavior.
4. Extend the same layers for US3 delete behavior.
5. Finish README and quickstart validation after the CRUD surface is complete.

### Team Strategy

1. One developer can complete Setup and Foundational work first.
2. After that, the test tasks within each user story can be split across team members.
3. Repository, service, and router tasks should stay sequential within each story to avoid file conflicts in `app/repositories/student_repository.py`, `app/services/student_service.py`, and `app/routers/students.py`.

---

## Notes

- All tasks use the required checklist format with task IDs, optional `[P]` markers, story labels, and exact file paths.
- Shared blocking work is intentionally limited to pytest scaffolding, dependency wiring, and shared validation rules.
- The contract artifact in `specs/001-student-crud-api/contracts/student-crud.openapi.yaml` is treated as the design-time source the implementation and contract tests must match.