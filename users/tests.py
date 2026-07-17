from django.test import TestCase
from rest_framework.test import APIClient

from users.models import CustomUser


class CustomUserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_superuser_requires_phone_number(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_superuser(
                email='admin@example.com',
                password='secret123',
            )

    def test_login_with_email_credentials(self):
        user = CustomUser.objects.create_user(
            email='user@example.com',
            password='secret123',
            phone_number='',
            is_active=True,
        )

        response = self.client.post(
            '/api/v1/users/authorization/',
            {'email': user.email, 'password': 'secret123'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('key', response.data)

    def test_registration_without_phone_number_is_allowed(self):
        response = self.client.post(
            '/api/v1/users/registration/',
            {'email': 'new@example.com', 'password': 'secret123'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(CustomUser.objects.filter(email='new@example.com').exists())
