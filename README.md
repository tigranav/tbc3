# Flask Application Scaffold

This repository provides a minimal Flask application scaffold configured to use the existing `libs` PostgreSQL helper and a sample blueprint exposing basic endpoints.

## Prerequisites
- Python 3.11
- PostgreSQL instance accessible to the application

Install application dependencies in your virtual environment:

```bash
pip install flask psycopg2-binary celery redis
```

## Configuration
Database connection settings are read from the environment via `app.config.PostgresConfig`:

- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: empty)
- `POSTGRES_DB` (default: `postgres`)

You can also set `FLASK_SECRET_KEY` to override the default secret key.

### Celery configuration

Celery is configured via `app.config.CeleryConfig` and the following environment variables:

- `CELERY_BROKER_URL` (default: `redis://localhost:6379/0`; must point to a Redis instance or the app will raise a validation error)
- `CELERY_RESULT_BACKEND` (default: unset)
- `CELERY_DEFAULT_QUEUE` (default: `default`)
- `CELERY_TASK_ACKS_LATE` (default: `1` to acknowledge tasks after completion)
- `CELERY_TASK_TIME_LIMIT` (default: `300` seconds)
- `CELERY_TASK_ALWAYS_EAGER` (default: `0`; set to `1` for local, synchronous execution in tests)
- `CELERY_TASK_EAGER_PROPAGATES` (default: `1`)
- `CELERY_TASK_STORE_EAGER_RESULT` (default: `0`; set to `1` when you want eager results returned to API callers)

## Running the application
Export the environment variables you need, then start the Flask development server using the application factory:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=postgres

# In the project root
export FLASK_APP="app:create_app"
flask run --debug
```

Visit `http://localhost:5000/api/health` to verify the service is running. The `/api/db-status` endpoint attempts to connect to PostgreSQL using the configured credentials and will return an error if the database is unavailable.

To expose the development server to other machines (for example, from inside a container), bind to all interfaces with `--host` or the corresponding environment variable:

```bash
flask --app "app:create_app" run --host 0.0.0.0 --port 5000 --debug
# or
export FLASK_APP="app:create_app"
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
flask run --debug
```

## Background tasks with Celery

The application ships with a Celery app in `app/celery_app.py` and a sample task at `app/tasks/importer.py` that normalizes importer records. Queues are configured in `app.config.CeleryConfig` and default to the queue name found in `CELERY_DEFAULT_QUEUE` (the importer blueprint uses this when dispatching tasks).

Celery is intentionally limited to Redis as its broker. Provide a Redis URL via `CELERY_BROKER_URL` (e.g., `redis://redis:6379/0`); any other scheme will fail validation during app startup.

### Starting a worker

Run a worker that listens to the configured queue:

```bash
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_DEFAULT_QUEUE=importer
celery -A app.celery_app.celery worker --loglevel=info --queues=${CELERY_DEFAULT_QUEUE}
```

The `--queues` flag creates (or binds to) the named queue if your broker supports it. You can add more queues by extending `CELERY_DEFAULT_QUEUE` and `celery.conf.task_routes` in `app/extensions.py`.

### Sending tasks from the importer API

POST records to `/api/importer/ingest` with `"enqueue": true` to place work onto the Celery queue:

```bash
curl -X POST http://localhost:5000/api/importer/ingest \
  -H "Content-Type: application/json" \
  -d '{
        "source": "cli-example",
        "enqueue": true,
        "records": [
          {"id": 1, "payload": "  Hello "},
          {"id": 2, "payload": "World"}
        ]
      }'
```

The endpoint returns task IDs for each queued record. When `CELERY_TASK_ALWAYS_EAGER=1` (useful in local development and tests), tasks execute immediately and the response includes their processed payloads. In production you can track task status using Celery result backends or the task IDs exposed in the response.

## Running with Docker Compose

This repository includes a simple `docker-compose.yml` that wires Redis as the Celery broker, a Flask web container, and a Celery worker. Build and start the stack with:

```bash
docker compose up --build
```

Services:

- `web`: runs `flask run` bound to `0.0.0.0:5000`.
- `worker`: runs `celery -A app.celery_app.celery worker --loglevel=info --queues=${CELERY_DEFAULT_QUEUE}`.
- `redis`: provides the required Redis broker on `redis://redis:6379/0`.

The default queue is `importer`. If you change `CELERY_DEFAULT_QUEUE`, both `web` and `worker` services pick it up from the shared environment and the worker binds to the same queue name. Use the importer API with `"enqueue": true` to publish tasks into that queue after the stack starts.

## Testing
Run the available tests with pytest:

```bash
pytest
```
