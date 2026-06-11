# LOS API MVP

Minimal FastAPI API with PostgreSQL and Docker, exposing CRUD for `student` and `classroom` tables.

## Student table

- `id`
- `name`

## Classroom table

- `id`
- `start_year` (YYYY)
- `end_year` (YYYY)
- `name` (derived `"{start_year}-{end_year}"`)

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

## Example payload

```json
{
  "name": "Alice"
}
```

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
  -d '{"name":"Alice"}'

curl http://localhost:8000/students
curl http://localhost:8000/students/1

curl -X PUT http://localhost:8000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated"}'

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

## Run locally without Docker

1. Create a PostgreSQL database.
2. Set `DATABASE_URL`.
3. Install dependencies:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```