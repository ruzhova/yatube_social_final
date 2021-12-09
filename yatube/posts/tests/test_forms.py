import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='MeredithPalmer')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.new_group = Group.objects.create(
            title='Название новой группы Тест2',
            slug='slugslug'
        )
        cls.user_group = Group.objects.create(
            title='Название группы Тест',
            slug='slugtest',
        )
        cls.post_created = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.user_group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_posts_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        image_const = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        user_image = SimpleUploadedFile(
            name='small.gif',
            content=image_const,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.user_group.pk,
            'image': user_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                author=self.author,
                group=self.user_group.pk,
                image='posts/small.gif',
            ).exists()
        )

    def test_form_posts_edit(self):
        """Валидная форма редактирует, а не создает запись в Post."""
        posts_count = Post.objects.count()
        image_const = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        new_image = SimpleUploadedFile(
            name='big.gif',
            content=image_const,
            content_type='image/gif'
        )
        form_data = {
            'text': 'NewText',
            'group': self.new_group.pk,
            'image': new_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post_created.pk]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post_created.pk])
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='NewText',
                author=self.author,
                group=self.new_group.pk,
                image='posts/big.gif',
            ).exists()
        )
