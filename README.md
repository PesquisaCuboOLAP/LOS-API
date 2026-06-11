# LOS API MVP

Minimal FastAPI API with PostgreSQL and Docker, exposing full CRUD for the `student` table.

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
- `POST /classrooms`  — creates a classroom (returns 409 if the same `start_year`+`end_year` already exists)
- `GET /classrooms`
- `PUT /classrooms/{classroom_id}`
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

When creating a classroom the API validates whether a classroom for the same `start_year` and `end_year` already exists. If it does, the request returns HTTP 409 Conflict with a message: `"A classroom for that period already exists"`.

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