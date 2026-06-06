from django.test import SimpleTestCase
from django.urls import reverse


class DashboardTests(SimpleTestCase):
    def test_dashboard_renders(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Servers")
        self.assertContains(response, "Tickets")

    def test_health_endpoint(self):
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
