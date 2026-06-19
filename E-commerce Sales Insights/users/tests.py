from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import CustomUserCreationForm


class CustomUserTests(TestCase):
    def test_user_id_is_assigned_on_create(self):
        user = get_user_model().objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="testpass123",
        )

        self.assertIsNotNone(user.user_id)
        self.assertGreaterEqual(user.user_id, 100000)
        self.assertLessEqual(user.user_id, 999999)


class SignupFormTests(TestCase):
    def test_public_signup_does_not_offer_admin_role(self):
        form = CustomUserCreationForm()

        role_values = [value for value, _label in form.fields["role"].choices]

        self.assertNotIn("admin", role_values)
        self.assertIn("analyst", role_values)
        self.assertIn("viewer", role_values)

    def test_public_signup_rejects_posted_admin_role(self):
        form = CustomUserCreationForm(data={
            "username": "admin-attempt",
            "email": "admin-attempt@example.com",
            "role": "admin",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)
