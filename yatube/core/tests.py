from http import HTTPStatus

from django.test import Client, TestCase


class ViewTestClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates_urlsp_names = {
            '/nonexist-page/': 'core/404.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_error_page(self):
        """"Проверка ответа страницы."""
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_template_page(self):
        """Проверка корректности использования шаблона."""
        for address, template in self.templates_urlsp_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
