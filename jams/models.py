from django.db import models


class JamJar(models.Model):
    sheet_id = models.CharField(max_length=80, unique=True)
    jam_type = models.CharField(max_length=120, blank=True)
    fruit = models.CharField(max_length=120, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    origin = models.CharField(max_length=120, blank=True, db_index=True)
    big = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=120, blank=True, db_index=True)
    date = models.DateField(null=True, blank=True, db_index=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-year", "sheet_id"]
        indexes = [
            models.Index(fields=["jam_type"]),
            models.Index(fields=["fruit"]),
        ]

    def __str__(self):
        label = " ".join(part for part in [self.jam_type, self.fruit] if part)
        return f"{self.sheet_id} {label}".strip()


class JamStorageSyncState(models.Model):
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    imported = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Jam storage sync state"
        verbose_name_plural = "Jam storage sync state"

    def __str__(self):
        if self.last_successful_sync_at:
            synced_at = self.last_successful_sync_at
            return f"Jam storage synced at {synced_at:%Y-%m-%d %H:%M}"
        return "Jam storage not synced yet"

    @classmethod
    def current(cls):
        state, _ = cls.objects.get_or_create(pk=1)
        return state
