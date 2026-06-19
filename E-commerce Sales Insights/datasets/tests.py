from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from analytics.cleaning_engine import calculate_quality_score
from .models import Dataset


class DatasetModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="dataset-owner",
            email="owner@example.com",
            password="testpass123",
        )

    def test_saving_active_dataset_deactivates_existing_active_dataset(self):
        first = Dataset.objects.create(
            name="First",
            uploaded_by=self.user,
            file=ContentFile(b"order_id,revenue\n1,10\n", name="first.csv"),
            is_active=True,
        )

        second = Dataset.objects.create(
            name="Second",
            uploaded_by=self.user,
            file=ContentFile(b"order_id,revenue\n2,20\n", name="second.csv"),
            is_active=True,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)

    def test_quality_score_penalizes_missing_required_columns(self):
        issues = {
            "missing_values": {},
            "duplicate_count": 0,
            "total_rows": 10,
            "invalid_date_count": 0,
            "negative_revenue_count": 0,
            "data_type_warnings": [],
        }

        score, grade = calculate_quality_score(issues, ["order_id", "revenue"])

        self.assertLess(score, 100)
        self.assertIn(grade, ["Good", "Needs Review", "Poor"])

    def test_viewer_cannot_upload_dataset(self):
        viewer = get_user_model().objects.create_user(
            username="viewer-datasets",
            email="viewer-datasets@example.com",
            password="testpass123",
            role="viewer",
        )
        self.client.force_login(viewer)

        response = self.client.get(reverse("datasets:upload"))

        self.assertEqual(response.status_code, 403)
