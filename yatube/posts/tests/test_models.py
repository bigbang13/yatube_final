from django.test import TestCase

from ..models import Group, Post, User

TEST_USERNAME: str = 'auth'
GROUP_TITLE: str = 'Тестовая группа'
GROUP_SLUG: str = 'test-slug'
GROUP_DESC: str = 'Тестовое описание'
POST_TEXT: str = 'Тестовый текст'
TEXT_MULTIPLIER: int = 10


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESC
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT * TEXT_MULTIPLIER,
        )
        cls.field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        cls.field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }

    def test_models_have_correct_object_names_post(self):
        """Проверка str класса Post."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_models_have_correct_object_names_group(self):
        """Проверка str класса Group."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_models_have_correct_verbose_names(self):
        """Проверка правильности verbose_name."""
        post = PostModelTest.post
        for field, expected_value in self.field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_models_have_correct_help_text(self):
        """Проверка правильности help_text."""
        post = PostModelTest.post
        for field, expected_value in self.field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
