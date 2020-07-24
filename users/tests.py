from django.test import TestCase, Client
from posts.models import User


class TestStringMethod(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah", email="connor@yandex.ru", password="sarah"
        )

    def test_profile(self):
        response = self.client.get("/sarah/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(response.context["author"].username, self.user.username)
