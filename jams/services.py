import csv
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

import httpx
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from jams.models import JamJar, JamStorageSyncState


class JamStorageSyncError(Exception):
    pass


@dataclass(frozen=True)
class SyncResult:
    imported: int = 0
    updated: int = 0
    skipped: int = 0


FIELD_ALIASES = {
    "sheet_id": {
        "id",
        "uid",
        "uniqueid",
        "unique id",
        "identificator",
        "cod",
        "nr",
        "numar",
    },
    "jam_type": {"type", "tip"},
    "fruit": {"fruit", "fruct", "fructe"},
    "year": {"year", "an"},
    "origin": {"origin", "origine", "provenienta"},
    "big": {"big", "large", "mare"},
    "status": {"status", "stare"},
    "date": {"date", "data"},
}

TRUE_VALUES = {"1", "true", "yes", "y", "da", "x", "mare", "big", "large"}


def fetch_jam_storage_csv() -> str:
    url = _csv_export_url()
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()
    return response.text


def sync_jam_storage(csv_text: str | None = None) -> SyncResult:
    state = JamStorageSyncState.current()

    try:
        source = csv_text if csv_text is not None else fetch_jam_storage_csv()
        result = _import_csv(source)
    except (httpx.HTTPError, csv.Error, UnicodeDecodeError, ValueError) as exc:
        message = _safe_error_message(exc)
        state.last_error = message
        state.save(update_fields=["last_error", "updated_at"])
        raise JamStorageSyncError(message) from exc

    state.last_successful_sync_at = timezone.now()
    state.imported = result.imported
    state.updated = result.updated
    state.skipped = result.skipped
    state.last_error = ""
    state.save(
        update_fields=[
            "last_successful_sync_at",
            "imported",
            "updated",
            "skipped",
            "last_error",
            "updated_at",
        ]
    )
    return result


def jam_storage_is_stale() -> bool:
    state = JamStorageSyncState.current()
    if not JamJar.objects.exists() or state.last_successful_sync_at is None:
        return True

    age = timezone.now() - state.last_successful_sync_at
    return age.total_seconds() >= settings.JAM_STORAGE_REFRESH_SECONDS


def filtered_jam_jars(filters: dict):
    jars = JamJar.objects.all()

    if filters.get("type"):
        jars = jars.filter(jam_type=filters["type"])
    if filters.get("fruit"):
        jars = jars.filter(fruit=filters["fruit"])
    if filters.get("year") and filters["year"].isdigit():
        jars = jars.filter(year=int(filters["year"]))
    if filters.get("origin"):
        jars = jars.filter(origin=filters["origin"])
    if filters.get("status"):
        jars = jars.filter(status=filters["status"])
    if filters.get("date"):
        date_filter = parse_date(filters["date"])
        if date_filter is not None:
            jars = jars.filter(date=date_filter)
    if filters.get("big") in {"true", "false"}:
        jars = jars.filter(big=filters["big"] == "true")

    return jars


def filter_options():
    return {
        "types": _distinct_values("jam_type"),
        "fruits": _distinct_values("fruit"),
        "years": list(
            JamJar.objects.exclude(year__isnull=True)
            .order_by("-year")
            .values_list("year", flat=True)
            .distinct()
        ),
        "origins": _distinct_values("origin"),
        "statuses": _distinct_values("status"),
    }


def _import_csv(csv_text: str) -> SyncResult:
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("Jam Storage CSV does not contain headers.")

    header_map = _header_map(reader.fieldnames)
    imported = 0
    updated = 0
    skipped = 0

    with transaction.atomic():
        for row in reader:
            normalized = _normalize_row(row, header_map)
            if normalized is None:
                skipped += 1
                continue

            _, created = JamJar.objects.update_or_create(
                sheet_id=normalized["sheet_id"],
                defaults={
                    "jam_type": normalized["jam_type"],
                    "fruit": normalized["fruit"],
                    "year": normalized["year"],
                    "origin": normalized["origin"],
                    "big": normalized["big"],
                    "status": normalized["status"],
                    "date": normalized["date"],
                    "raw_data": normalized["raw_data"],
                },
            )
            if created:
                imported += 1
            else:
                updated += 1

    return SyncResult(imported=imported, updated=updated, skipped=skipped)


def _normalize_row(row: dict, header_map: dict[str, str]) -> dict | None:
    sheet_id = _clean_value(_mapped_value(row, header_map, "sheet_id"))
    if not sheet_id:
        return None

    return {
        "sheet_id": sheet_id,
        "jam_type": _clean_value(_mapped_value(row, header_map, "jam_type")),
        "fruit": _clean_value(_mapped_value(row, header_map, "fruit")),
        "year": _parse_year(_mapped_value(row, header_map, "year")),
        "origin": _clean_value(_mapped_value(row, header_map, "origin")),
        "big": _parse_bool(_mapped_value(row, header_map, "big")),
        "status": _clean_value(_mapped_value(row, header_map, "status")),
        "date": _parse_date(_mapped_value(row, header_map, "date")),
        "raw_data": {key: value for key, value in row.items() if key is not None},
    }


def _header_map(headers: list[str]) -> dict[str, str]:
    normalized_headers = {_normalize_header(header): header for header in headers}
    mapped = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            header = normalized_headers.get(_normalize_header(alias))
            if header is not None:
                mapped[field] = header
                break
    return mapped


def _mapped_value(row: dict, header_map: dict[str, str], field: str):
    header = header_map.get(field)
    if header is None:
        return ""
    return row.get(header, "")


def _clean_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_year(value) -> int | None:
    cleaned = _clean_value(value)
    if not cleaned:
        return None
    match = re.search(r"\d{4}", cleaned)
    if match:
        return int(match.group(0))
    if cleaned.isdigit():
        return int(cleaned)
    return None


def _parse_bool(value) -> bool:
    return _normalize_header(_clean_value(value)) in TRUE_VALUES


def _parse_date(value):
    cleaned = _clean_value(value)
    if not cleaned:
        return None

    parsed = parse_date(cleaned)
    if parsed is not None:
        return parsed

    for date_format in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue
    return None


def _normalize_header(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def _distinct_values(field: str) -> list[str]:
    return list(
        JamJar.objects.exclude(**{field: ""})
        .order_by(field)
        .values_list(field, flat=True)
        .distinct()
    )


def _csv_export_url() -> str:
    return (
        "https://docs.google.com/spreadsheets/d/"
        f"{settings.JAM_STORAGE_SHEET_ID}/export"
        f"?format=csv&gid={settings.JAM_STORAGE_SHEET_GID}"
    )


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"Jam Storage sync failed with HTTP {exc.response.status_code}."
    if isinstance(exc, httpx.HTTPError):
        return "Jam Storage sync failed while contacting Google Sheets."
    return f"Jam Storage sync failed: {exc}"
