# Quickstart: Student CRUD API

## Purpose

This quickstart captures how to validate the feature during implementation. It is aligned with the current repository layout and the planned architecture refactor.

## Prerequisites

- Docker and Docker Compose available locally
- Python 3.12 for local non-container runs
- PostgreSQL port `5432` and API port `8000` available when using Docker Compose

## Current Baseline Verification

Start the existing stack:

```bash
docker compose up --build
```

Check health and API docs:

```bash
curl http://localhost:8000/health
open http://localhost:8000/docs
```

Exercise the current CRUD endpoints manually:

```bash
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}'

curl http://localhost:8000/students
curl http://localhost:8000/students/1

curl -X PUT http://localhost:8000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated"}'

curl -X DELETE http://localhost:8000/students/1
```

## Target Validation After Implementation

Install the updated dependencies and run tests:

```bash
pip install -r requirements.txt
pytest
```

Recommended focused validation sequence during implementation:

```bash
pytest tests/unit/test_student_service.py
pytest tests/integration/test_student_persistence.py
pytest tests/contract/test_students_api.py
```

## Expected Outcomes

- `POST /students` returns `201` with `id` and `name`
- `GET /students` returns a stable list ordered by `id`
- `GET /students/{student_id}` returns `200` for existing rows and `404` for missing ids
- `PUT /students/{student_id}` updates names without creating new rows for missing ids
- `DELETE /students/{student_id}` returns `204` and subsequent reads return `404`
- Blank or whitespace-only names are rejected with `422`
- OpenAPI docs remain available at `/docs` and describe the same schemas and status codes as the contract file

## Notes

- Docker Compose service names remain `api` and `db`.
- Containerized database connections must continue using host `db` in `DATABASE_URL`.
- The implementation should keep startup schema creation in place unless a future feature explicitly introduces migrations.