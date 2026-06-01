# Data Model: Student CRUD API

## Entity: Student

**Purpose**: Persist the core record managed by the API.

**Backing Table**: `student`

| Field | Type | Source | Rules |
|-------|------|--------|-------|
| `id` | integer | Database-generated primary key | Required, unique, positive, assigned on create |
| `name` | string | Client input | Required, max length 255, must not be blank after trimming |

## API Request Models

### `StudentCreate`

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | 1-255 visible characters after trimming; reject empty or whitespace-only input |

### `StudentUpdate`

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | Same validation rules as create |

## API Response Models

### `StudentRead`

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | Stable identifier returned after persistence |
| `name` | string | Persisted student name |

### `ErrorResponse`

| Field | Type | Notes |
|-------|------|-------|
| `detail` | string | Human-readable error message such as `Student not found` or a validation error summary |

## Relationships

- No cross-entity relationships in this feature.

## State Transitions

### Create

- Input: valid `StudentCreate`
- Result: new `Student` row persisted with generated `id`

### Read

- Input: existing `student_id` or collection request
- Result: one `StudentRead` record or ordered list of `StudentRead` records

### Update

- Input: existing `student_id` plus valid `StudentUpdate`
- Result: existing row updated in place; no upsert behavior

### Delete

- Input: existing `student_id`
- Result: row removed; endpoint returns `204 No Content`

## Validation Rules

- `student_id` must be an integer path parameter.
- Missing student ids return `404 Not Found` and must not create or mutate data.
- Invalid request bodies return `422 Unprocessable Entity` via FastAPI/Pydantic validation.
- Student lists are returned in ascending `id` order to keep responses deterministic.

## Repository And Service Ownership

- Repository owns SQLAlchemy reads/writes and commit/refresh orchestration for the `student` table.
- Service owns business semantics: delegating persistence, surfacing not-found outcomes, and preserving API contract expectations.
- Router owns HTTP translation only: dependency resolution, status codes, and response models.