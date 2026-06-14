# LOS API MVP

Minimal FastAPI API with PostgreSQL and Docker, exposing CRUD for `student` and `classroom` tables.

## Student table

- `id`
- `name`
- `classroom_id` (required foreign key to `classroom.id`)

Each student must belong to exactly one classroom.

## Classroom table

- `id`
- `start_year` (YYYY)
- `end_year` (YYYY)
- `name` (derived `"{start_year}-{end_year}"`)

Each classroom can have zero or many students.

## Import students from CSV

You can bulk import students into a classroom with:

`POST /classrooms/{classroom_id}/students/import`

The endpoint expects a CSV upload with this required header:

```csv
name
```

Rules:

- The classroom must exist.
- The CSV must include the `name` column.
- Invalid CSV files or missing required columns return HTTP 400 Bad Request.
- Empty rows are skipped.
- Each non-empty row creates one `Student` and is assigned to the classroom from the route.
- The response returns a summary with the number of imported students.

Example CSV file: [examples/students_import.csv](examples/students_import.csv)

## Import learning objectives from CSV

You can bulk import learning objectives into a classroom with:

`POST /classrooms/{classroom_id}/learning-objectives/import/{semester}`

Example:

`POST /classrooms/1/learning-objectives/import/1`

The endpoint expects a CSV upload with these required headers:

```csv
Code,Learning Strand,Goal Short Name,Learning Objective,Learning Objective Keywords,Challenge
```

Rules:

- The classroom must exist.
- The `semester` route parameter must be a valid challenge semester (`1` to `4`).
- Missing goal short names are created automatically.
- Existing goal short names are reused, but the import fails with HTTP 409 if the CSV strand conflicts with the stored strand for that goal short name.
- Learning objectives are imported into the classroom from the route.
- Existing learning objectives in that same classroom are skipped by `code`, so the import is safe to repeat.
- Duplicate learning objective codes later in the same CSV file are skipped.
- Challenges are created or updated by unique `name` using the `Challenge` CSV column.
- If an existing challenge has `semester = null`, the import sets it from the route parameter.
- If an existing challenge already has a different semester, the import fails with HTTP 409.

The response returns an import summary with counts for created goal short names, imported learning objectives, skipped duplicates, and created or updated challenges.

## Run with Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Endpoints

- `GET /health`
- `POST /students`
- `GET /students`
- `GET /students/{student_id}`
- `PUT /students/{student_id}`
- `DELETE /students/{student_id}`
- `POST /classrooms`  — returns 409 if the same `start_year`+`end_year` already exists
- `GET /classrooms`
- `PUT /classrooms/{classroom_id}` — returns 409 if another classroom already has the same `start_year`+`end_year`
- `DELETE /classrooms/{classroom_id}`
- `POST /classrooms/{classroom_id}/students/import`
- `POST /classrooms/{classroom_id}/learning-objectives/import/{semester}`
- `POST /goal-short-names` — returns 409 if the name already exists
- `POST /challenges` — returns 409 if the name already exists

## Example payload

```json
{
  "name": "Alice",
  "classroom_id": 1
}
```

Student create/update requests require a valid `classroom_id`.

## Classroom payload

Create / Update classroom JSON:

```json
{
  "start_year": "2024",
  "end_year": "2025"
}
```

The API enforces uniqueness for classroom period (`start_year` + `end_year`) on both create and update:

- Create (`POST /classrooms`): if the same period already exists, returns HTTP 409 Conflict.
- Update (`PUT /classrooms/{classroom_id}`): if another classroom already uses the same period, returns HTTP 409 Conflict.

Conflict message:

`"A classroom for that period already exists"`

## Example requests

```bash
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","classroom_id":1}'

curl http://localhost:8000/students
curl http://localhost:8000/students/1

curl -X PUT http://localhost:8000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated","classroom_id":1}'

curl -X DELETE http://localhost:8000/students/1
```

## Classroom example requests

```bash
curl -X POST http://localhost:8000/classrooms \
  -H "Content-Type: application/json" \
  -d '{"start_year":"2024","end_year":"2025"}'

curl http://localhost:8000/classrooms

curl -X PUT http://localhost:8000/classrooms/1 \
  -H "Content-Type: application/json" \
  -d '{"start_year":"2024","end_year":"2026"}'

curl -X DELETE http://localhost:8000/classrooms/1
```

Deleting a classroom that still has students returns HTTP 409 Conflict.

## CSV import example

```bash
curl -X POST http://localhost:8000/classrooms/1/students/import \
  -F "file=@examples/students_import.csv"

curl -X POST http://localhost:8000/classrooms/1/learning-objectives/import/1 \
  -F "file=@examples/25_26\ LG_LO\ [new]-All\ -\ Challenge\ (1).csv"
```

## Run locally without Docker

1. Create a PostgreSQL database.
2. Set `DATABASE_URL`.
3. Install dependencies:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Existing databases

The app currently creates tables with SQLAlchemy `create_all` on startup and does not use Alembic migrations yet. New constraints such as the unique challenge name constraint are applied automatically in fresh environments and in tests, but they are not retrofitted onto an already-created database table. If you already have a local database created before this change, recreate it or apply the constraint manually before relying on the import behavior.