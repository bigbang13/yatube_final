from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User

TEST_USERNAME: str = 'auth'
TEST_USERNAME2: str = 'User'
GROUP_TITLE: str = 'Тестовая группа'
GROUP_SLUG: str = 'test-slug'
GROUP_DESC: str = 'Тестовое описание'
POST_TEXT: str = 'Тестовый текст'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESC,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
        cls.public_urls_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.private_urls_names = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.urls_names_redir_guest = {
            f'/posts/{cls.post.id}/edit/': (
                f'/auth/login/?next=/posts/{cls.post.id}/edit/'),
            '/create/': '/auth/login/?next=/create/',
            '/follow/': '/auth/login/?next=/follow/',
            f'/profile/{cls.user}/follow/': (
                f'/auth/login/?next=/profile/{cls.user}/follow/'),
            f'/profile/{cls.user}/unfollow/': (
                f'/auth/login/?next=/profile/{cls.user}/unfollow/'),
        }

    def setUp(self):
        self.guest_client = Client()
        self.user2 = User.objects.create(username=TEST_USERNAME2)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_public_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        for address in list(self.public_urls_names):
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_guest(self):
        """Страницы недоступны гостевому пользователю."""
        for address, move_address in self.urls_names_redir_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response, (move_address))

    def test_private_urls_exists_at_desired_location(self):
        """Страницы доступны авториз пользователю."""
        for address in list(self.private_urls_names):
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.public_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.private_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_edit_authorized(self):
        """Страница edit недоступна авториз польз не автору поста."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/'))

    def test_url_unexist_page(self):
        """Проверка несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
