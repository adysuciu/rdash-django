from django.conf import settings
from django.http import JsonResponse
from django.views.generic import TemplateView, View

from sensors.services import (
    ThingSpeakConfigError,
    readings_are_stale,
    recent_readings,
    sync_thingspeak_readings,
)


class SensorsView(TemplateView):
    template_name = "sensors/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["refresh_seconds"] = settings.SENSOR_REFRESH_SECONDS
        return context


class SensorReadingsApiView(View):
    def get(self, _request):
        error = ""
        if readings_are_stale():
            try:
                sync_thingspeak_readings()
            except ThingSpeakConfigError as exc:
                error = str(exc)

        readings = [
            {
                "recorded_at": reading.recorded_at.isoformat(),
                "label": reading.recorded_at.strftime("%H:%M"),
                "temperature": float(reading.temperature),
                "humidity": float(reading.humidity),
            }
            for reading in recent_readings()
        ]
        return JsonResponse({"readings": readings, "error": error})
