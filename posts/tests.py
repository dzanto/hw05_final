from django.test import TestCase, Client, override_settings
from .models import Post, User, Follow, Comment
from django.urls import reverse
from PIL import Image


class TestPostApp(TestCase):

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
        self.client.post(reverse("new_post"), data={"text": "Hello world", "author": self.auth_user})
        response = self.client.get(reverse("profile", kwargs={"username": self.auth_user.username}))
        self.assertContains(response, "Hello world")

    def test_redirect_post(self):
        self.client.post(reverse("new_post"), data={"text": "Hello world", "author": self.not_auth_user})
        response = self.client.get(reverse("profile", kwargs={"username": self.not_auth_user.username}))
        self.assertEqual(len(response.context["page"]), 0)

    def test_add_post(self):
        self.post = Post.objects.create(text='Hello world', author=self.auth_user)
        response = self.client.get(reverse("index"))
        self.assertIn(self.post, response.context["page"])

        response = self.client.get(reverse("profile", kwargs={"username": self.auth_user.username}))
        self.assertIn(self.post, response.context["page"])

        response = self.client.get(reverse("post", kwargs={"username": self.auth_user.username, "post_id": self.post.id}))
        self.assertEqual(self.post, response.context["post"])

    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

    @override_settings(CACHES=CACHES)
    def test_edit_post(self):
        self.post = Post.objects.create(text='Hello world', author=self.auth_user)
        response = self.client.get(
            reverse("post", kwargs={"username": self.auth_user.username, "post_id": self.post.id}))
        self.assertContains(response, "Hello world")
        self.client.post(reverse(
            "post_edit", kwargs={"username": self.auth_user.username, "post_id": self.post.id}),
            data={"text": "Goodbye world", "author": self.auth_user})
        response = self.client.get(
            reverse("post", kwargs={"username": self.auth_user.username, "post_id": self.post.id}))
        self.assertContains(response, "Goodbye world")

    def test_handler404(self):
        response = self.client.get("/404/")
        self.assertEqual(response.status_code, 404)

    @override_settings(CACHES=CACHES)
    def test_img(self):

        img = Image.new('RGBA', (200, 200), 'white')
        img.save('posts/media/square.png')

        self.post = Post.objects.create(text='Post without image', author=self.auth_user)
        with open('posts/media/square.png', 'rb') as img:
            self.client.post(reverse(
                "post_edit", kwargs={"username": self.auth_user.username, "post_id": self.post.id}),
                data={'author': self.auth_user, 'text': 'post with image', 'image': img})

        urls = [
            {"name": "post", "kwargs": {"username": self.auth_user.username, "post_id": self.post.id}},
            {"name": "index", "kwargs": {}},
            {"name": "profile", "kwargs": {"username": self.auth_user.username}},
        ]

        for url in urls:
            response = self.client.get(reverse(url["name"], kwargs=url["kwargs"]))
            self.assertContains(response, "<img")

    def test_not_img(self):
        self.post = Post.objects.create(text='Post without image', author=self.auth_user)
        with open('posts/media/file.txt', 'rb') as img:
            self.client.post(reverse(
                "post_edit", kwargs={"username": self.auth_user.username, "post_id": self.post.id}),
                data={'author': self.auth_user, 'text': 'post with image', 'image': img})
        response = self.client.get(
            reverse("post", kwargs={"username": self.auth_user.username, "post_id": self.post.id}))
        self.assertNotContains(response, "<img")

    def test_cash(self):
        self.post = Post.objects.create(text='Test cash', author=self.auth_user)
        response = self.client.get(reverse("index"))
        self.assertNotContains(response, "Test cash")

    def test_follow(self):
        self.post = Post.objects.create(text='Hello world from not_auth_user', author=self.not_auth_user)
        self.post = Post.objects.create(text='Hello world from auth_user', author=self.auth_user)

        self.client.get(reverse("profile_follow", kwargs={"username": self.not_auth_user.username}))
        self.client.get(reverse("profile_follow", kwargs={"username": self.auth_user.username}))

        response = self.client.get(reverse("follow_index"))
        self.assertContains(response, "Hello world from not_auth_user")

        self.client.get(reverse("profile_unfollow", kwargs={"username": self.not_auth_user.username}))

        response = self.client.get(reverse("follow_index"))
        self.assertNotContains(response, "Hello world from not_auth_user")

        self.client.logout()
        self.client.force_login(self.not_auth_user)

        self.client.get(reverse("profile_follow", kwargs={"username": self.not_auth_user.username}))
        response = self.client.get(reverse("follow_index"))
        self.assertNotContains(response, "Hello world from auth_user")

    def test_comment(self):
        self.post = Post.objects.create(text='Hello world', author=self.auth_user)
        self.client.post(reverse(
            "add_comment", kwargs={"username": self.post.author.username, "post_id": self.post.id}),
            data={"text": "My comment"}, follow=True)
        response = self.client.get(
            reverse("post", kwargs={"username": self.post.author.username, "post_id": self.post.id}))
        self.assertContains(response, "My comment")
