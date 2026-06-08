from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from sensors.models import SensorReading

THINGSPEAK_BASE_URL = "https://api.thingspeak.com"


class ThingSpeakConfigError(Exception):
    pass


@dataclass(frozen=True)
class SyncResult:
    imported: int = 0
    updated: int = 0
    skipped: int = 0


def fetch_thingspeak_payload() -> dict:
    if not settings.THINGSPEAK_CHANNEL_ID or not settings.THINGSPEAK_READ_API_KEY:
        raise ThingSpeakConfigError(
            "ThingSpeak channel id and read API key must be configured."
        )

    url = f"{THINGSPEAK_BASE_URL}/channels/{settings.THINGSPEAK_CHANNEL_ID}/feeds.json"
    response = httpx.get(
        url,
        params={
            "api_key": settings.THINGSPEAK_READ_API_KEY,
            "results": settings.THINGSPEAK_RESULTS,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def sync_thingspeak_readings(payload: dict | None = None) -> SyncResult:
    payload = payload if payload is not None else fetch_thingspeak_payload()
    imported = 0
    updated = 0
    skipped = 0

    for feed in payload.get("feeds", []):
        reading = _normalize_feed(feed)
        if reading is None:
            skipped += 1
            continue

        _, created = SensorReading.objects.update_or_create(
            entry_id=reading["entry_id"],
            defaults={
                "recorded_at": reading["recorded_at"],
                "temperature": reading["temperature"],
                "humidity": reading["humidity"],
            },
        )
        if created:
            imported += 1
        else:
            updated += 1

    return SyncResult(imported=imported, updated=updated, skipped=skipped)


def readings_are_stale() -> bool:
    latest = SensorReading.objects.order_by("-created_at").first()
    if latest is None:
        return True

    age = timezone.now() - latest.created_at
    return age.total_seconds() >= settings.SENSOR_REFRESH_SECONDS


def recent_readings(limit: int | None = None):
    limit = limit or settings.THINGSPEAK_RESULTS
    readings = SensorReading.objects.order_by("-recorded_at")[:limit]
    return reversed(list(readings))


def _normalize_feed(feed: dict) -> dict | None:
    entry_id = feed.get("entry_id")
    recorded_at = _parse_recorded_at(feed.get("created_at"))
    temperature = _parse_decimal(feed.get("field1"))
    humidity = _parse_decimal(feed.get("field2"))

    if (
        entry_id is None
        or recorded_at is None
        or temperature is None
        or humidity is None
    ):
        return None

    return {
        "entry_id": int(entry_id),
        "recorded_at": recorded_at,
        "temperature": temperature,
        "humidity": humidity,
    }


def _parse_decimal(value: str | int | float | None) -> Decimal | None:
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _parse_recorded_at(value: str | None):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.utc)
    return parsed
