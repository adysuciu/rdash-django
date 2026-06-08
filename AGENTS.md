# Agent Guide

## Project Map
- `config/` contains Django settings, URL routing, ASGI, and WSGI.
- `dashboard/` contains the demo homepage view, template, CSS, test cases, and fixture-like constants.
- `sensors/` contains ThingSpeak integration, persisted sensor readings, the Sensors page, API endpoint, tests, and sync command.
- `Dockerfile`, `compose.yaml`, and `.dockerignore` define the container workflow.
- `pyproject.toml` is the source of dependency and tool configuration.

## Safe Commands
- `uv sync --dev` installs dependencies.
- `uv run pytest` runs request tests.
- `uv run ruff check .` runs lint checks.
- `uv run python manage.py check` runs Django system checks.
- `uv run python manage.py collectstatic --noinput` verifies static asset collection.
- `uv run python manage.py sync_thingspeak_readings` fetches recent ThingSpeak readings when sensor env vars are configured.
- `docker compose up --build` builds and runs the containerized demo.

## Mutation Rules
- Keep dashboard demo data in `dashboard/data.py` so agents can inspect it without scraping templates.
- Do not reintroduce Bower, Less compilation, or Node unless the UI is intentionally redesigned.
- Prefer plain Django templates and static files for this demo.
- Keep ThingSpeak keys in environment variables only; never commit real API keys.
- Do not commit local `.env`, `db.sqlite3`, `staticfiles/`, or Python cache output.

## Verification
After code changes, run the smallest useful set first:
1. `uv run pytest`
2. `uv run ruff check .`
3. `uv run python manage.py check`
4. `uv run python manage.py collectstatic --noinput`

For container changes, also run `docker build .` and then verify `/healthz/` through `docker compose up --build`.
