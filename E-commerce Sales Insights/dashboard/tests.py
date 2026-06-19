from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import SavedFilterView


class DashboardRouteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="testpass123",
            role="analyst",
        )

    def test_protected_dashboard_routes_redirect_anonymous_users(self):
        protected_routes = [
            reverse("dashboard:index"),
            reverse("dashboard:forecast"),
            reverse("dashboard:export", args=["csv"]),
        ]

        for url in protected_routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("users:login"), response["Location"])

    def test_documentation_routes_render(self):
        doc_routes = [
            reverse("dashboard:about"),
            reverse("dashboard:methodology"),
            reverse("dashboard:dataset_info"),
            reverse("dashboard:flow"),
            reverse("dashboard:viva"),
        ]

        for url in doc_routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_forecast_route_renders_without_active_dataset(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:forecast"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Active Dataset")

    def test_save_filter_view_creates_named_view(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("dashboard:save_filter"), {
            "name": "North Region Electronics",
            "query_string": "region=North&category=Electronics",
        })

        self.assertEqual(response.status_code, 302)
        saved = SavedFilterView.objects.get(user=self.user)
        self.assertEqual(saved.name, "North Region Electronics")
        self.assertEqual(saved.query_string, "region=North&category=Electronics")

    def test_viewer_cannot_export_reports(self):
        viewer = get_user_model().objects.create_user(
            username="viewer",
            email="viewer2@example.com",
            password="testpass123",
            role="viewer",
        )
        self.client.force_login(viewer)

        response = self.client.get(reverse("dashboard:export", args=["csv"]))

        self.assertEqual(response.status_code, 403)
