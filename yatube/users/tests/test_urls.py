from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import User


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.templates_url_names_pub = {
            '/auth/logout/': 'users/logged_out.html',
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/reset/NA/5xd-a050ec649dba14159f27/': (
                'users/password_reset_confirm.html'),
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        cls.templates_url_names_auth = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }
        cls.urls_names = {
            '/auth/password_change/': (
                '/auth/login/?next=/auth/password_change/'),
            '/auth/password_change/done/': (
                '/auth/login/?next=/auth/password_change/done/'),
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        for address in list(self.templates_url_names_pub):
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect(self):
        """Проверка редиректа со страниц."""
        for address, move_address in self.urls_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response, (move_address))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names_pub.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_usr_auth(self):
        """URL-адрес использует соответствующий шаблон при смене пароля"""
        for address, template in self.templates_url_names_auth.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
