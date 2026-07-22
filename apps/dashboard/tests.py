from django.test import SimpleTestCase
from django.urls import resolve, reverse


class DashboardUrlTests(SimpleTestCase):
    def test_dashboard_home_url_resolves_to_dashboard_view(self):
        match = resolve("/dashboard/")

        self.assertEqual(reverse("dashboard:home"), "/dashboard/")
        self.assertEqual(match.view_name, "dashboard:home")
