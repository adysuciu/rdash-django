from django.db import models


class SensorReading(models.Model):
    entry_id = models.PositiveIntegerField(unique=True)
    recorded_at = models.DateTimeField(db_index=True)
    temperature = models.DecimalField(max_digits=6, decimal_places=2)
    humidity = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["recorded_at"]

    def __str__(self):
        return f"{self.recorded_at:%Y-%m-%d %H:%M} {self.temperature}C {self.humidity}%"
