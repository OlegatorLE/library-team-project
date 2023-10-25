from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from book.models import Book
from book.serializers import BookSerializer

BOOK_URL = reverse("book:book-list")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_book(**params):
    defaults = {
        "title": "Test Title",
        "author": "Test Author",
        "cover": "hard",
        "inventory": 20,
        "daily_fee": "12.2",
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def detail_url(book_id):
    return reverse("book:book-detail", args=[book_id])


class PublicBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_book(self):
        res = self.client.get(BOOK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_book(self):
        book = sample_book()

        url = detail_url(book.id)
        response = self.client.get(url)

        serializer = BookSerializer(book, many=False)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class PrivateBookApiTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user(email="test@test.com", password="testpassword")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_books(self):
        sample_book()

        response = self.client.get(BOOK_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_movie(self):
        book = sample_book()

        url = detail_url(book.id)
        response = self.client.get(url)

        serializer = BookSerializer(book, many=False)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_post_book(self):
        payload = {
            "title": "Test Title",
            "author": "Test Author",
            "cover": "hard",
            "inventory": 20,
            "daily_fee": "12.2",
        }

        response = self.client.post(BOOK_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_book(self):
        book = sample_book()

        url = detail_url(book.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email="admin@test.com",
            password="testpassword",
            is_staff=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_post_book(self):
        payload = {
            "title": "Test Title",
            "author": "Test Author",
            "cover": "hard",
            "inventory": 20,
            "daily_fee": "12.2",
        }

        response = self.client.post(BOOK_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_book(self):
        book = sample_book()
        url = detail_url(book.id)

        payload = {
            "title": "New Test Title",
            "author": "Author Sample",
            "cover": "soft",
            "inventory": 25,
            "daily_fee": "15.20",
        }

        response = self.client.put(url, payload)

        print(response.status_code)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_book(self):
        book = sample_book()

        url = detail_url(book.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
