# FieldData Weather Alerts

Backend challenge implementation for a climate alert system built with `FastAPI`, `SQLAlchemy`, `PostgreSQL`, `Alembic`, and an async worker process.

## Overview

Users configure weather alerts for their fields by choosing:

- a weather event type
- a probability threshold
- an optional event-intensity threshold
- one or more validity windows

A background worker evaluates stored forecasts against those alerts and persists notifications whenever a forecast matches all configured conditions.

## Main Decisions

- Forecasts are modeled **per field**.
- The application uses a **default seeded user** instead of real authentication.
- Alerts support **multiple validity windows**.
- Validity windows can be:
  - relative: `HOUR`, `DAY`, `WEEK`, `MONTH`, `YEAR`
  - absolute: `start_datetime` to `end_datetime`
- Relative windows are evaluated from the **current evaluation time**, not from alert creation time.
- Datetimes are expected and returned using the `-03:00` offset.
- Intensity comparison behavior is derived by `event_type`.
- Notifications are deduplicated by `alert_id + forecast_id`.
- Notifications are persisted in the database; no WhatsApp integration is implemented.

## Event Types

Each event type has a predefined intensity unit and comparison rule.

| Event type | Intensity unit | Threshold rule |
| --- | --- | --- |
| `RAIN` | `MM_PER_HOUR` | forecast intensity `>=` threshold |
| `STRONG_WIND` | `KM_PER_HOUR` | forecast intensity `>=` threshold |
| `HAIL` | `MM` | forecast intensity `>=` threshold |
| `FROST` | `CELSIUS` | forecast intensity `<=` threshold |

## Architecture

The project is split into three runtime services:

- `postgres`: database
- `api`: FastAPI HTTP service
- `worker`: APScheduler-based background evaluator

There are also two one-off Compose services:

- `migrate`: runs `alembic upgrade head`
- `seed`: inserts the default demo user, fields, forecasts, and a sample alert

Alembic is intentionally **not** embedded inside the Postgres container. The migration tooling runs from the application image, which is the standard practice because schema evolution belongs to the application, not the database server process.

## Data Model

### `users`

- `id`
- `name`
- `phone` (required, unique)
- `created_at`
- `updated_at`

### `fields`

- `id`
- `user_id`
- `name`
- `created_at`
- `updated_at`

### `weather_forecasts`

- `id`
- `field_id`
- `forecast_datetime`
- `event_type`
- `probability_percent`
- `intensity_value`
- `created_at`
- `updated_at`

### `weather_alerts`

- `id`
- `user_id`
- `field_id`
- `event_type`
- `probability_threshold_percent`
- `intensity_threshold_value`
- `is_active`
- `created_at`
- `updated_at`

### `alert_validity_windows`

- `id`
- `alert_id`
- `kind`
- `relative_value`
- `relative_unit`
- `start_datetime`
- `end_datetime`
- `created_at`
- `updated_at`

### `notifications`

- `id`
- `alert_id`
- `forecast_id`
- `user_id`
- `field_id`
- `event_type`
- `forecast_datetime`
- `trigger_probability_percent`
- `trigger_intensity_value`
- `message`
- `created_at`

## API Endpoints

### Health

- `GET /health`

### Fields

- `GET /fields`
- `POST /fields`

### Alerts

- `GET /alerts`
- `POST /alerts`
- `GET /alerts/{alert_id}`
- `PATCH /alerts/{alert_id}`
- `DELETE /alerts/{alert_id}`

### Forecasts

- `GET /forecasts`

### Notifications

- `GET /notifications`

### Internal job trigger

- `POST /internal/jobs/evaluate-alerts`

## Example Alert Payload

```json
{
  "field_id": 1,
  "event_type": "RAIN",
  "probability_threshold_percent": 80,
  "intensity_threshold_value": 8,
  "validity_windows": [
    {
      "kind": "RELATIVE",
      "relative_value": 1,
      "relative_unit": "WEEK"
    },
    {
      "kind": "ABSOLUTE",
      "start_datetime": "2026-04-10T00:00:00-03:00",
      "end_datetime": "2026-04-17T23:59:59-03:00"
    }
  ]
}
```

## Running With Docker Compose

### Prerequisites

- Docker
- Docker Compose

### Start the full stack

```bash
docker compose up --build
```

This brings up:

- Postgres
- migration service
- seed service
- API on `http://localhost:8000`
- worker process

If your local Compose version does not support `service_completed_successfully` in `depends_on`, run the bootstrap sequence manually:

```bash
docker compose up -d postgres
docker compose run --rm migrate
docker compose run --rm seed
docker compose up --build api worker
```

Swagger UI will be available at:

```text
http://localhost:8000/docs
```

### Re-run migrations manually

```bash
docker compose run --rm migrate
```

### Re-run seed manually

```bash
docker compose run --rm seed
```

## Running Locally Without Docker

### 1. Install dependencies

```bash
python -m pip install --user -e .[dev]
```

### 2. Set environment variables

You can copy `.env.example` into `.env` and adjust values if needed.

### 3. Run migrations

```bash
python -m alembic upgrade head
```

### 4. Seed demo data

```bash
python -m app.seeds.bootstrap
```

### 5. Start the API

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Start the worker in a separate terminal

```bash
python -m app.workers.main
```

## Testing

### Unit tests

```bash
python -m pytest tests/unit -q
```

### Integration tests

Integration tests require a Postgres database URL via `TEST_DATABASE_URL`.

Example:

```bash
set TEST_DATABASE_URL=postgresql+asyncpg://fielddata:fielddata@localhost:5432/fielddata_test
python -m pytest tests/integration -q
```

If `TEST_DATABASE_URL` is not set, the integration tests are skipped.

## Notes And Assumptions

- Forecast data is mocked through the bootstrap script.
- Absolute validity windows must use timezone-aware datetimes with the `-03:00` offset.
- Relative window evaluation uses rolling windows from the moment the evaluator runs.
- Phone validation is intentionally minimal for now.
- `TODO`: enforce E.164 phone validation once country-specific normalization rules are defined.
