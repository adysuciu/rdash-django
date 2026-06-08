# rdash-django

A modern Django 6 rebuild of a legacy rdash dashboard demo. The app keeps the spirit of the original static Bootstrap dashboard while using current Django, Python, Docker, and agent-friendly project conventions.

## Stack

- Python 3.12-3.14, with Docker targeting Python 3.14
- Django 6.0
- WhiteNoise for static files
- Gunicorn for container runtime
- SQLite for local and demo containers
- `uv` for local dependency management
- Plotly.js for sensor charts

## Local Development

```bash
uv sync --dev
uv run python manage.py migrate
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Docker

```bash
docker compose up --build
```

The app listens on http://127.0.0.1:8000/ and exposes a health check at http://127.0.0.1:8000/healthz/.

## Sensors

The Sensors page reads temperature and humidity from ThingSpeak through Django, stores normalized readings in SQLite, and renders two Plotly.js charts.

Configure these variables in `.env` or Compose:

- `THINGSPEAK_CHANNEL_ID`
- `THINGSPEAK_READ_API_KEY`
- `THINGSPEAK_RESULTS`, default `100`
- `SENSOR_REFRESH_SECONDS`, default `60`

Temperature is read from ThingSpeak `field1`; humidity is read from `field2`.

```bash
uv run python manage.py migrate
uv run python manage.py sync_thingspeak_readings
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/sensors/.

## Verification

```bash
uv run pytest
uv run ruff check .
uv run python manage.py check
uv run python manage.py collectstatic --noinput
docker build .
```

## Configuration

Copy `.env.example` to `.env` for local overrides. Supported variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `DJANGO_SETTINGS_MODULE`
- `THINGSPEAK_CHANNEL_ID`
- `THINGSPEAK_READ_API_KEY`
- `THINGSPEAK_RESULTS`
- `SENSOR_REFRESH_SECONDS`

## Agent Notes

See `AGENTS.md` for the project map, safe commands, and mutation rules. Demo data lives in `dashboard/data.py` so coding agents can reason about the dashboard without parsing HTML.
