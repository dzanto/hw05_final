from django.test import TestCase, Client, override_settings
from .models import Post, User, Follow, Comment
from django.urls import reverse


class TestStringMethod(TestCase):

    def setUp(self):
        self.client = Client()
        self.not_auth_user = User.objects.create_user(
            username="terminator", email="terminator@yandex.ru", password="terminator"
        )
        self.auth_user = User.objects.create_user(
            username="sarah", email="connor@yandex.ru", password="sarah"
        )
        self.client.force_login(self.auth_user)

    def test_new_post(self):
        self.client.post("/new/", {"text": "Hello world", "author": self.auth_user})
        response = self.client.get(f"/{self.auth_user.username}/")
#        response = self.client.post(reverse("new_post"), data={"text": "Hello world", "author": self.auth_user})
        self.assertContains(response, "Hello world")

    def test_redirect_post(self):
        self.client.post("/new/", {"text": "Hello world", "author": self.not_auth_user})
        response = self.client.get(f"/{self.not_auth_user.username}/")
        self.assertEqual(len(response.context["page"]), 0)

    def test_add_post(self):
        self.post = Post.objects.create(text='Hello world', author=self.auth_user)
        response = self.client.get("")
        self.assertIn(self.post, response.context["page"])

        response = self.client.get(f"/{self.auth_user.username}/")
        self.assertIn(self.post, response.context["page"])

        response = self.client.get(f"/{self.auth_user.username}/{self.post.id}/")
        self.assertEqual(self.post, response.context["post"])

    def test_edit_post(self):
        self.post = Post.objects.create(text='Hello world', author=self.auth_user)
        response = self.client.get(f"/{self.auth_user.username}/{self.post.id}/")
        self.assertContains(response, "Hello world")
        self.client.post(
            f"/{self.auth_user.username}/{self.post.id}/edit/",
            {"text": "Goodbye world", "author": self.auth_user}
        )
        response = self.client.get(f"/{self.auth_user.username}/{self.post.id}/")
        self.assertContains(response, "Goodbye world")

    def test_handler404(self):
        response = self.client.get("/404/")
        self.assertEqual(response.status_code, 404)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    })
    def test_img(self):
        self.post = Post.objects.create(text='Post without image', author=self.auth_user)
        with open('posts/media/file.jpg', 'rb') as img:
            self.client.post(f"/{self.auth_user.username}/{self.post.id}/edit/",
                         {'author': self.auth_user, 'text': 'post with image', 'image': img})
        response = self.client.get(f"/{self.auth_user.username}/{self.post.id}/")
        self.assertContains(response, "<img")

        response = self.client.get("")
        self.assertContains(response, "<img")

        response = self.client.get(f"/{self.auth_user.username}/")
        self.assertContains(response, "<img")

        response = self.client.get(f"/{self.auth_user.username}/{self.post.id}/")
        self.assertContains(response, "<img")

    def test_not_img(self):
        self.post = Post.objects.create(text='Post without image', author=self.auth_user)
        with open('posts/media/file.txt', 'rb') as img:
            self.client.post(f"/{self.auth_user.username}/{self.post.id}/edit/",
                             {'author': self.auth_user, 'text': 'post with image', 'image': img})
        response = self.client.get(f"/{self.auth_user.username}/{self.post.id}/")
        self.assertNotContains(response, "<img")

    def test_cash(self):
        self.post = Post.objects.create(text='Test cash', author=self.auth_user)
        response = self.client.get("")
        self.assertNotContains(response, "Test cash")

    def test_follow(self):
        self.post = Post.objects.create(text='Hello world from not_auth_user', author=self.not_auth_user)
        self.post = Post.objects.create(text='Hello world from auth_user', author=self.auth_user)

        self.client.get(f"/{self.not_auth_user.username}/follow/")
        self.client.get(f"/{self.auth_user.username}/follow/")

        response = self.client.get("/follow/")
        self.assertContains(response, "Hello world from not_auth_user")

        self.client.get(f"/{self.not_auth_user.username}/unfollow/")

        response = self.client.get("/follow/")
        self.assertNotContains(response, "Hello world from not_auth_user")

        self.client.logout()
        self.client.force_login(self.not_auth_user)

        self.client.get(f"/{self.not_auth_user.username}/follow/")
        response = self.client.get("/follow/")
        self.assertNotContains(response, "Hello world from auth_user")

    def test_comment(self):
        self.post = Post.objects.create(text='Hello world', author=self.auth_user)
        self.client.post(f"/{self.post.author.username}/{self.post.id}/comment/",
                          {"text": "My comment"}, follow=True)
        response = self.client.get(f"/{self.post.author.username}/{self.post.id}/")
        self.assertContains(response, "My comment")
