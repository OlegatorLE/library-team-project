from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse


class UserManagerTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser@mail.com", password="password"
        )
        self.superuser = get_user_model().objects.create_superuser(
            email="testsuperuser@mail.com", password="password"
        )
        self.client.force_authenticate(user=self.superuser)

    def test_create_user(self):
        self.assertEqual(self.user.email, "testuser@mail.com")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        self.assertEqual(self.superuser.email, "testsuperuser@mail.com")
        self.assertTrue(self.superuser.is_active)
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)

    def test_user_str(self):
        self.assertEqual(str(self.user), "testuser@mail.com")


class UserAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser@api.com", password="password"
        )
        self.superuser = get_user_model().objects.create_superuser(
            email="testsuperuser@api.com", password="password"
        )
        self.client.force_authenticate(user=self.superuser)

    def test_create_user_via_api(self):
        url = reverse("user:create")
        data = {"email": "test@api.com", "password": "password", "first_name": "Test", "last_name": "User"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(get_user_model().objects.count(), 3)

    def test_retrieve_user_via_api(self):
        url = reverse("user:manage")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.superuser.email)

    def test_token_obtain(self):
        url = reverse("user:token_obtain_pair")
        data = {"email": self.superuser.email, "password": "password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
