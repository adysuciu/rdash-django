from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from dashboard.views import DashboardView


def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
]
