from django.core.management.base import BaseCommand

from sensors.services import sync_thingspeak_readings


class Command(BaseCommand):
    help = "Fetch recent ThingSpeak temperature and humidity readings."

    def handle(self, *args, **options):
        result = sync_thingspeak_readings()
        self.stdout.write(
            self.style.SUCCESS(
                "ThingSpeak sync complete: "
                f"{result.imported} imported, "
                f"{result.updated} updated, "
                f"{result.skipped} skipped."
            )
        )
