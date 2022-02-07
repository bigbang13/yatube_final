import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User
from posts.views import POSTS_ON_PAGE

NUM_TEST_POSTS: int = 12
ALL_POSTS_COUNT: int = 13
NUM_POSTS_SEC_PAGE = ALL_POSTS_COUNT - POSTS_ON_PAGE
NUM_CHECK_POST: int = 13
TEST_USERNAME: str = 'auth'
TEST2_USERNAME: str = 'test2'
TEST3_USERNAME: str = 'test3'
GROUP_TITLE: str = 'Тестовая группа'
GROUP_SLUG: str = 'test-slug'
GROUP_DESC: str = 'Тестовое описание'
GROUP_NEW_TITLE: str = 'Заголовок новой группы'
GROUP_NEW_SLUG: str = 'test-new-slug'
GROUP_NEW_DESC: str = 'Описание новой группы'
POST_TEXT: str = 'Тестовый текст'
POST_NEW_TEXT: str = 'Another text'
POST_CACHE_TEXT: str = 'Test cache text'
POST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME)
        cls.user2 = User.objects.create_user(username=TEST2_USERNAME)
        cls.user3 = User.objects.create_user(username=TEST3_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESC,
        )
        cls.group2 = Group.objects.create(
            title=GROUP_NEW_TITLE,
            slug=GROUP_NEW_SLUG,
            description=GROUP_NEW_DESC,
        )
        cls.object_list = [
            Post(
                author=cls.user,
                text=f'{POST_NEW_TEXT} {i}',
                group=cls.group
            )
            for i in range(NUM_TEST_POSTS)
        ]
        cls.posts_list = Post.objects.bulk_create(cls.object_list)
        cls.post1 = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=POST_IMAGE,
                content_type='image/gif'
            )
        )
        cls.pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': f'{cls.post1.group.slug}'}),
            reverse('posts:profile', kwargs={
                'username': f'{cls.post1.author}'}),
        ]
        cls.values = {
            'text': cls.post1.text,
            'group': cls.group,
            'author': cls.user,
            'image': cls.post1.image
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client_author = Client()
        self.auth_client_author.force_login(self.user)
        self.auth_client = Client()
        self.auth_client.force_login(self.user2)
        self.auth_client_notfollow = Client()
        self.auth_client_notfollow.force_login(self.user3)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post1.id}'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post1.id}'}
            ): 'posts/create_post.html',
            reverse(
                'posts:follow_index'
            ): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth_client_author.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0]
        for attr, expected in self.values.items():
            value = getattr(first_obj, attr)
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        second_obj = response.context['posts'][0]
        post1_text = second_obj.text
        self.assertEqual(post1_text, POST_TEXT)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_client_author.get(
            reverse(
                'posts:group_list', kwargs={'slug': GROUP_SLUG}
            )
        )
        first_obj = response.context['page_obj'][0]
        for attr, expected in self.values.items():
            value = getattr(first_obj, attr)
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        second_obj = response.context['group']
        group1_slug = second_obj.slug
        self.assertEqual(group1_slug, GROUP_SLUG)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth_client_author.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user}'}
            )
        )
        first_obj = response.context['page_obj'][0]
        for attr, expected in self.values.items():
            value = getattr(first_obj, attr)
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        second_obj = response.context['user_profile']
        profile1_username = second_obj.username
        self.assertEqual(profile1_username, TEST_USERNAME)
        third_obj = response.context['following']
        self.assertEqual(third_obj, False)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth_client_author.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post1.id}'}
            )
        )
        first_obj = response.context['post']
        post1_text = first_obj.text
        self.assertEqual(post1_text, POST_TEXT)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_client_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post1.id}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        values = {
            'post_id': NUM_CHECK_POST,
            'is_edit': True,
        }
        for value, expected in values.items():
            with self.subTest(value=value):
                obj = response.context[value]
                self.assertEqual(obj, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth_client_author.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_on_page(self):
        """Проверяем наличие поста с группой на странице."""
        for reverse_name in self.pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertIn(self.post1, response.context['page_obj'])

    def test_post_with_group_not_on_other_group_page(self):
        """Проверяем отсутствие поста на странице с не присв ему группой."""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.group2.slug}'}
            )
        )
        self.assertNotIn(self.post1, response.context['page_obj'])

    def test_first_page_contains_ten_records(self):
        """Проверяем количество постов на первой странице."""
        for reverse_name in self.pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(
                    response.context['page_obj']), POSTS_ON_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверяем количество постов на второй странице."""
        for reverse_name in self.pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(
                    response.context['page_obj']), NUM_POSTS_SEC_PAGE)

    def test_index_cache_content(self):
        """Шаблон index правильно кэшируется"""
        cache.clear()
        post_cache = Post.objects.create(
            author=self.user,
            text=POST_CACHE_TEXT,
        )
        response = self.auth_client_author.get(reverse('posts:index'))
        page_context = response.context['page_obj'][0]
        page_content = response.content
        self.assertEqual(page_context.text, post_cache.text)
        Post.objects.get(id=post_cache.id).delete()
        new_response = self.auth_client_author.get(reverse('posts:index'))
        page_new_content = new_response.content
        self.assertEqual(page_content, page_new_content)
        cache.clear()
        clear_response = self.auth_client_author.get(reverse('posts:index'))
        page_clear_content = clear_response.content
        self.assertNotEqual(page_content, page_clear_content)

    def test_follow_user(self):
        """Проверяем оформление подписки на автора."""
        author = self.user
        self.assertEqual(self.user2.follower.count(), 0)
        self.auth_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{author}'}
            )
        )
        self.assertEqual(self.user2.follower.count(), 1)
        self.assertTrue(
            Follow.objects.filter(user=self.user2, author=author).exists()
        )
        self.auth_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{author}'}
            )
        )
        self.assertEqual(self.user2.follower.count(), 1)

    def test_unfollow_user(self):
        """Проверяем оформление отписки от автора."""
        author = self.user
        self.assertEqual(self.user2.follower.count(), 0)
        self.auth_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{author}'}
            )
        )
        self.assertEqual(self.user2.follower.count(), 1)
        self.auth_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': f'{author}'}
            )
        )
        self.assertEqual(self.user2.follower.count(), 0)
        self.assertFalse(
            Follow.objects.filter(user=self.user2, author=author).exists()
        )

    def test_follow_index_user(self):
        """Проверяем появление постов у подписанных авторов"""
        author = self.user
        self.assertEqual(self.user2.follower.count(), 0)
        self.auth_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{author}'}
            )
        )
        self.assertEqual(self.user2.follower.count(), 1)
        response = self.auth_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        page_context = response.context['page_obj'][0]
        self.assertEqual(page_context.text, self.post1.text)
        response = self.auth_client_notfollow.get(
            reverse(
                'posts:follow_index'
            )
        )
        posts_count_follow_index = len(response.context['page_obj'])
        self.assertEqual(posts_count_follow_index, 0)
