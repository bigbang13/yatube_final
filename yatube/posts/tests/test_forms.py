import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEST_USERNAME: str = 'auth'
GROUP_TITLE: str = 'Тестовая группа'
GROUP_SLUG: str = 'test-slug'
GROUP_DESC: str = 'Тестовое описание'
GROUP_NEW_TITLE: str = 'Заголовок из формы'
COMMENT_TEXT: str = 'Тестовый комментарий'
POST_TEXT: str = 'Тестовый текст'
POST_NEW_TEXT: str = 'Another text'
POST_EDIT_TEXT: str = 'new_test_text'
POST_GUEST_TEXT: str = 'Guest text'
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
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESC,
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_create_new_post(self):
        """Проверка создания нового поста авт пользователем."""
        posts_count = Post.objects.count()
        upload_image = SimpleUploadedFile(
            name='small.gif',
            content=POST_IMAGE,
            content_type='image/gif'
        )
        form_data = {
            'text': POST_NEW_TEXT,
            'group': self.group.id,
            'image': upload_image,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': f'{self.user}'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=POST_NEW_TEXT,
                author=self.user,
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_cant_create_null_text_post(self):
        """Проверка невозможности создания пустого поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': GROUP_NEW_TITLE,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        """Проверка возможности редактирования поста автором."""
        posts_count = Post.objects.count()
        form_data = {
            'text': POST_EDIT_TEXT,
            'group': self.group.id,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={
                'post_id': f'{self.post1.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': f'{self.post1.id}'}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=POST_EDIT_TEXT,
            ).exists()
        )

    def test_cant_create_text_post_guest(self):
        """Проверка невозможности создания поста гостем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': POST_GUEST_TEXT,
            'group': GROUP_NEW_TITLE,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text='Guest text',
            ).exists()
        )

    def test_cant_edit_post_guest(self):
        """Проверка невозможности редактирования поста гостем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': POST_GUEST_TEXT,
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': f'{self.post1.id}'}),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        self.assertRedirects(
            response, f'{login_url}?next=/posts/{self.post1.id}/edit/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=POST_GUEST_TEXT,
            ).exists()
        )

    def test_cant_comment_post_guest(self):
        """Проверка невозможности комментирования поста гостем."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': f'{self.post1.id}'}),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        self.assertRedirects(
            response, f'{login_url}?next=/posts/{self.post1.id}/comment/')
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text=COMMENT_TEXT,
            ).exists()
        )

    def test_create_new_comment(self):
        """Проверка создания нового коммента авт пользователем."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.authorized_client_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post1.id}'}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': f'{self.post1.id}'}
        ))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=COMMENT_TEXT,
                author=self.user,
            ).exists()
        )
