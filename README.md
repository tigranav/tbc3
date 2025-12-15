# Flask Application Scaffold

This repository provides a minimal Flask application scaffold configured to use the existing `libs` PostgreSQL helper and a sample blueprint exposing basic endpoints.

## Prerequisites
- Python 3.11
- PostgreSQL instance accessible to the application

Install application dependencies in your virtual environment:

```bash
pip install flask psycopg2-binary
```

## Configuration
Database connection settings are read from the environment via `app.config.PostgresConfig`:

- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: empty)
- `POSTGRES_DB` (default: `postgres`)

You can also set `FLASK_SECRET_KEY` to override the default secret key.

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

## Testing
Run the available tests with pytest:

```bash
pytest
```
