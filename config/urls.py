from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from dashboard.views import DashboardView
from jams.views import JamStorageView
from sensors.views import SensorReadingsApiView, SensorsView


def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("sensors/", SensorsView.as_view(), name="sensors"),
    path("jam-storage/", JamStorageView.as_view(), name="jam-storage"),
    path(
        "api/sensors/readings/",
        SensorReadingsApiView.as_view(),
        name="sensor-readings-api",
    ),
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
]
