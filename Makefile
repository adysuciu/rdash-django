.PHONY: setup test lint check collectstatic run sync-sensors docker-build docker-up

setup:
	uv sync --dev

test:
	uv run pytest

lint:
	uv run ruff check .

check:
	uv run python manage.py check

collectstatic:
	uv run python manage.py collectstatic --noinput

run:
	uv run python manage.py runserver 0.0.0.0:8000

sync-sensors:
	uv run python manage.py sync_thingspeak_readings

docker-build:
	docker build .

docker-up:
	docker compose up --build
