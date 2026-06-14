from datetime import timedelta
from unittest.mock import Mock, patch

import httpx
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from jams.models import JamJar, JamStorageSyncState
from jams.services import JamStorageSyncError, jam_storage_is_stale, sync_jam_storage

SAMPLE_CSV = """id,tip,fruct,an,origine,mare,status,data,raft
J-001,dulceata,capsuni,2026,maman,da,in storage,2026-06-01,A1
J-002,gem,prune,2025,mama tereza,,consumed,01.05.2025,B2
"""


class JamJarModelTests(TestCase):
    def test_duplicate_sheet_id_updates_existing_jar(self):
        sync_jam_storage("id,tip,fruct\nJ-001,dulceata,capsuni\n")

        result = sync_jam_storage("id,tip,fruct\nJ-001,gem,prune\n")

        self.assertEqual(result.updated, 1)
        self.assertEqual(JamJar.objects.count(), 1)
        jar = JamJar.objects.get(sheet_id="J-001")
        self.assertEqual(jar.jam_type, "gem")
        self.assertEqual(jar.fruit, "prune")

    def test_parsed_fields_are_stored(self):
        sync_jam_storage(SAMPLE_CSV)

        jar = JamJar.objects.get(sheet_id="J-001")

        self.assertEqual(jar.jam_type, "dulceata")
        self.assertEqual(jar.fruit, "capsuni")
        self.assertEqual(jar.year, 2026)
        self.assertEqual(jar.origin, "maman")
        self.assertTrue(jar.big)
        self.assertEqual(jar.status, "in storage")
        self.assertEqual(jar.date.isoformat(), "2026-06-01")
        self.assertEqual(jar.raw_data["raft"], "A1")


class JamStorageServiceTests(TestCase):
    def test_valid_rows_are_imported(self):
        result = sync_jam_storage(SAMPLE_CSV)

        self.assertEqual(result.imported, 2)
        self.assertEqual(JamJar.objects.count(), 2)

    def test_rows_without_unique_id_are_skipped(self):
        result = sync_jam_storage("id,tip,fruct\n,dulceata,capsuni\nJ-001,gem,prune\n")

        self.assertEqual(result.imported, 1)
        self.assertEqual(result.skipped, 1)

    def test_mare_maps_to_boolean(self):
        sync_jam_storage(SAMPLE_CSV)

        self.assertTrue(JamJar.objects.get(sheet_id="J-001").big)
        self.assertFalse(JamJar.objects.get(sheet_id="J-002").big)

    @patch("jams.services.httpx.get")
    def test_sync_errors_are_recorded_without_url_or_secret_details(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("boom")

        with self.assertRaises(JamStorageSyncError):
            sync_jam_storage()

        state = JamStorageSyncState.current()
        self.assertIn("Jam Storage sync failed", state.last_error)
        self.assertNotIn("docs.google.com", state.last_error)

    def test_fresh_successful_sync_is_not_stale(self):
        sync_jam_storage(SAMPLE_CSV)

        self.assertFalse(jam_storage_is_stale())


class JamStorageViewTests(TestCase):
    def setUp(self):
        sync_jam_storage(SAMPLE_CSV)

    def test_page_renders_table_and_filter_form(self):
        response = self.client.get(reverse("jam-storage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jam Storage")
        self.assertContains(response, 'name="fruit"')
        self.assertContains(response, "J-001")

    def test_filters_work_for_all_fields(self):
        filters = {
            "type": "dulceata",
            "fruit": "capsuni",
            "year": "2026",
            "origin": "maman",
            "big": "true",
            "status": "in storage",
            "date": "2026-06-01",
        }

        response = self.client.get(reverse("jam-storage"), filters)

        self.assertContains(response, "J-001")
        self.assertNotContains(response, "J-002")

    @patch("jams.views.sync_jam_storage")
    def test_stale_local_data_triggers_sync(self, mock_sync):
        state = JamStorageSyncState.current()
        state.last_successful_sync_at = timezone.now() - timedelta(days=8)
        state.save()

        self.client.get(reverse("jam-storage"))

        mock_sync.assert_called_once_with()

    @patch("jams.views.sync_jam_storage")
    def test_fresh_local_data_does_not_refetch(self, mock_sync):
        self.client.get(reverse("jam-storage"))

        mock_sync.assert_not_called()

    @patch("jams.views.sync_jam_storage")
    def test_sync_error_keeps_existing_rows_visible(self, mock_sync):
        mock_sync.side_effect = JamStorageSyncError("Jam Storage sync failed.")
        state = JamStorageSyncState.current()
        state.last_successful_sync_at = timezone.now() - timedelta(days=8)
        state.save()

        response = self.client.get(reverse("jam-storage"))

        self.assertContains(response, "J-001")
        self.assertContains(response, "Jam Storage sync failed.")


class SyncJamStorageCommandTests(TestCase):
    @patch("jams.management.commands.sync_jam_storage.sync_jam_storage")
    def test_command_reports_sync_counts(self, mock_sync):
        mock_sync.return_value = Mock(imported=2, updated=1, skipped=3)

        with patch("sys.stdout") as stdout:
            call_command("sync_jam_storage")

        self.assertIn("2 imported", stdout.write.call_args_list[0].args[0])
