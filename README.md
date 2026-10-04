# Dataset Request Desk

A small internal platform for managing robotics dataset requests, episode inventory, assignments, delivery, and client acceptance.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Auth:** JWT access tokens + scrypt password hashing
- **Frontend:** React + Vite
- **Ops:** Docker Compose
- **Tests:** pytest

## Run the whole system

Requirements: Docker Desktop / Docker Engine + Compose.

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The API container automatically runs migrations and creates the seed users from `candidate-pack/seed/users.json`.

### Seed accounts

| Role | Email | Password |
|---|---|---|
| admin | admin@example.com | admin123 |
| operator | ops1@example.com | ops123 |
| operator | ops2@example.com | ops123 |
| client | client-a@example.com | client123 |
| client | client-b@example.com | client123 |

Passwords are hashed before storage; the plaintext values only exist in the supplied seed file for local testing.

## Import episodes

Operators/admins can upload `candidate-pack/seed/episodes.csv` from the API docs or call the endpoint from a client:

```bash
curl -X POST http://localhost:8000/episodes/import \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@candidate-pack/seed/episodes.csv"
```

The importer normalizes task/quality casing and whitespace, accepts several date formats, rejects malformed/unknown/invalid records, skips duplicates, and returns counts/reasons. It is safe to run repeatedly.

## Tests

```bash
cd backend
pytest -q
```

## Main workflow

1. Client logs in and creates a request.
2. Operator starts it: `submitted -> in_progress`.
3. Operator assigns only `good`/`usable` episodes. An episode can belong to only one request.
4. Operator can deliver only after enough episodes are assigned.
5. Client accepts: `delivered -> accepted`, or rejects: `delivered -> rejected`.
6. Operator moves rejected work back to `in_progress` for rework.
7. Every status change is stored in `status_history`.

## Analytics

`GET /analytics?start=...&end=...` returns episodes/day/robot, request counts by status, median submitted-to-delivered time, and the top five task names by good episodes. Aggregation happens in SQL rather than loading all episodes into Python.

For millions of episodes, PostgreSQL indexes on `recorded_at`, `robot_id`, `quality`, request status, and history timestamps are the first line of defence. At larger scale I would add query plans/observability, composite/partial indexes based on real workloads, partition episodes by date if justified, and potentially a read replica or pre-aggregated analytics tables.

## Repository structure

```text
backend/
  app/
    routers/       HTTP endpoints
    services/      domain/import logic
    auth.py        password hashing + JWT
    models.py      relational schema
    schemas.py     API validation
    main.py        FastAPI app + structured request logs
  alembic/         migrations
  tests/           authorization/domain/import tests
frontend/
  src/main.jsx     small role-aware UI
candidate-pack/    supplied seed data
NOTES.md           engineering decisions and trade-offs
```

## Stretch item

No stretch item was selected. Given the time budget, correctness, tests, import idempotency, and explainability were prioritised.

## Frontend note
This version intentionally uses **plain HTML, CSS, and JavaScript** instead of React/Vite. Nginx only serves the static frontend files. The browser still talks to the FastAPI backend at `http://localhost:8000`.
