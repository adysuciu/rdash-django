from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from sensors.models import SensorReading
from sensors.services import ThingSpeakConfigError, sync_thingspeak_readings

SAMPLE_PAYLOAD = {
    "feeds": [
        {
            "created_at": "2026-06-06T10:00:00Z",
            "entry_id": 1,
            "field1": "22.50",
            "field2": "44.10",
        },
        {
            "created_at": "2026-06-06T10:15:00Z",
            "entry_id": 2,
            "field1": "23.00",
            "field2": "45.20",
        },
    ]
}


class SensorReadingModelTests(TestCase):
    def test_reading_stores_sensor_values(self):
        recorded_at = timezone.now()

        reading = SensorReading.objects.create(
            entry_id=10,
            recorded_at=recorded_at,
            temperature=Decimal("22.50"),
            humidity=Decimal("44.10"),
        )

        self.assertEqual(reading.entry_id, 10)
        self.assertEqual(reading.temperature, Decimal("22.50"))
        self.assertEqual(reading.humidity, Decimal("44.10"))

    def test_duplicate_entry_id_updates_existing_reading(self):
        payload = {
            "feeds": [
                {
                    "created_at": "2026-06-06T10:00:00Z",
                    "entry_id": 10,
                    "field1": "22.50",
                    "field2": "44.10",
                }
            ]
        }
        sync_thingspeak_readings(payload)
        payload["feeds"][0]["field1"] = "23.75"

        result = sync_thingspeak_readings(payload)

        self.assertEqual(result.updated, 1)
        self.assertEqual(SensorReading.objects.count(), 1)
        self.assertEqual(
            SensorReading.objects.get(entry_id=10).temperature,
            Decimal("23.75"),
        )


class ThingSpeakServiceTests(TestCase):
    def test_valid_feeds_are_parsed_and_saved(self):
        result = sync_thingspeak_readings(SAMPLE_PAYLOAD)

        self.assertEqual(result.imported, 2)
        self.assertEqual(SensorReading.objects.count(), 2)

    def test_invalid_or_blank_values_are_skipped(self):
        payload = {
            "feeds": [
                {
                    "created_at": "2026-06-06T10:00:00Z",
                    "entry_id": 1,
                    "field1": "",
                    "field2": "44.10",
                },
                {
                    "created_at": "2026-06-06T10:15:00Z",
                    "entry_id": 2,
                    "field1": "not-a-number",
                    "field2": "45.20",
                },
                {
                    "created_at": "2026-06-06T10:30:00Z",
                    "entry_id": 3,
                    "field1": "23.00",
                    "field2": None,
                },
            ]
        }

        result = sync_thingspeak_readings(payload)

        self.assertEqual(result.skipped, 3)
        self.assertEqual(SensorReading.objects.count(), 0)

    @override_settings(
        THINGSPEAK_CHANNEL_ID="12345",
        THINGSPEAK_READ_API_KEY="read-key",
        THINGSPEAK_RESULTS=2,
    )
    @patch("sensors.services.httpx.get")
    def test_fetch_uses_settings_without_hardcoded_credentials(self, mock_get):
        response = Mock()
        response.json.return_value = SAMPLE_PAYLOAD
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        sync_thingspeak_readings()

        mock_get.assert_called_once_with(
            "https://api.thingspeak.com/channels/12345/feeds.json",
            params={"api_key": "read-key", "results": 2},
            timeout=10,
        )

    @override_settings(THINGSPEAK_CHANNEL_ID="", THINGSPEAK_READ_API_KEY="")
    def test_missing_config_raises_clear_error(self):
        with self.assertRaises(ThingSpeakConfigError):
            sync_thingspeak_readings()


class SensorsViewTests(TestCase):
    def test_sensors_page_renders_chart_containers(self):
        response = self.client.get(reverse("sensors"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="temperature-chart"')
        self.assertContains(response, 'id="humidity-chart"')
        self.assertContains(response, "cdn.plot.ly")

    def test_readings_api_returns_ordered_json(self):
        sync_thingspeak_readings(SAMPLE_PAYLOAD)

        response = self.client.get(reverse("sensor-readings-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["error"], "")
        self.assertEqual(len(payload["readings"]), 2)
        self.assertEqual(payload["readings"][0]["temperature"], 22.5)
        self.assertEqual(payload["readings"][1]["humidity"], 45.2)

    @override_settings(THINGSPEAK_CHANNEL_ID="", THINGSPEAK_READ_API_KEY="")
    def test_readings_api_returns_non_secret_config_error(self):
        response = self.client.get(reverse("sensor-readings-api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["readings"], [])
        self.assertIn("must be configured", response.json()["error"])


class SyncThingSpeakCommandTests(TestCase):
    @patch("sensors.management.commands.sync_thingspeak_readings.sync_thingspeak_readings")
    def test_command_reports_sync_counts(self, mock_sync):
        mock_sync.return_value = Mock(imported=2, updated=1, skipped=3)

        with patch("sys.stdout") as stdout:
            call_command("sync_thingspeak_readings")

        self.assertIn("2 imported", stdout.write.call_args_list[0].args[0])
