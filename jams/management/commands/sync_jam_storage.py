from django.core.management.base import BaseCommand

from jams.services import sync_jam_storage


class Command(BaseCommand):
    help = "Fetch Jam Storage rows from the configured Google Sheet."

    def handle(self, *args, **options):
        result = sync_jam_storage()
        self.stdout.write(
            self.style.SUCCESS(
                "Jam Storage sync complete: "
                f"{result.imported} imported, "
                f"{result.updated} updated, "
                f"{result.skipped} skipped."
            )
        )
