from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post
from yatube.settings import NUM_OF_POSTS

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='JimHalpert')
        cls.user_not_author = User.objects.create_user(
            username='PamBeesly'
        )
        cls.user_group = Group.objects.create(
            title='Название группы Тест',
            slug='slugtest',
        )
        cls.image_const = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.user_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.image_const,
            content_type='image/gif'
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='interesting story',
            author=cls.user,
            group=cls.user_group,
            image=cls.user_image,
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.post.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_edit', args=[cls.post.pk]
            ): 'posts/create_post.html',
            reverse(
                'posts:post_detail', args=[cls.post.pk]
            ): 'posts/post_detail.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_pages_use_correct_templates(self):
        """
        Проверка, что во view-функциях используются правильные html-шаблоны.
        """
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_check(self, response):
        """Проверка контекста."""
        first_object = response.context['page_obj'][0]
        title_0 = first_object.author
        text_0 = first_object.text
        slug_0 = first_object.group
        image_0 = first_object.image
        self.assertEqual(title_0, self.user)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(slug_0, self.post.group)
        self.assertEqual(image_0, self.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.context_check(response)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}
            )
        )
        self.assertEqual(
            response.context.get('group').slug,
            self.post.group.slug
        )
        self.context_check(response)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(
            response.context.get('writer').username,
            self.user.username
        )
        self.context_check(response)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.pk])
        )
        self.assertEqual(response.context.get('post'), self.post)

    def form_check(self, response):
        """Проверка формы."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.form_check(response)

    def test_edit_post_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.pk])
        )
        self.form_check(response)
        self.assertEqual(response.context.get('editable_post'), self.post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='OscarMartinez')
        cls.client = Client()
        cls.client.force_login(cls.user_author)
        Post.objects.bulk_create([
            Post(
                text='post' + str(i),
                author=cls.user_author
            ) for i in range(13)
        ])

    def test_page_contains_records(self):
        """
        Проверка, что на первой странице находится 10 постов,
        а на второй странице 3 поста.
        """
        params = {
            reverse('posts:index'): NUM_OF_POSTS,
            (
                reverse('posts:index') + '?page=2'
            ): Post.objects.count() - NUM_OF_POSTS,
        }
        for adress, count in params.items():
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                (len(response.context['page_obj']), count)


class AdditionalVerification(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='MichaelScott')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user_author)
        cls.user_not_author = User.objects.create_user(username='ErinHannon')
        cls.auth_not_author = Client()
        cls.auth_not_author.force_login(cls.user_not_author)
        cls.not_follower = User.objects.create_user(username='Creed')
        cls.auth_not_foll = Client()
        cls.auth_not_foll.force_login(cls.not_follower)
        cls.client_group = Group.objects.create(
            title='Office',
            slug='slugclient',
        )
        cls.additional_group = Group.objects.create(
            title='NotOffice',
            slug='wrongslugt',
        )
        cls.newpost = Post.objects.create(
            text='great post!',
            author=cls.user_author,
            group=cls.client_group
        )

    def test_pages_contain_new_post(self):
        """
        Проверяет, содержится ли новый пост с группой на страницах
        index, group_list с введенной группой и profile пользователя.
        """
        responses = [
            self.auth_client.get(reverse('posts:index')),
            self.auth_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'slug': self.newpost.group.slug}
                )
            ),
            self.auth_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.newpost.author.username}
                )
            )
        ]
        for i in responses:
            self.assertIn(self.newpost, i.context['page_obj'])

    def test_pages_dont_contain_new_post(self):
        """
        Проверяет, не попал ли новый пост с группой на страницу
        group_list с не той группой.
        """
        failed_responses = self.auth_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.additional_group.slug}
            )
        )
        self.assertNotIn(self.newpost, failed_responses.context['page_obj'])

    def test_add_comment_check_authorized(self):
        """
        Проверка, что авторизированный пользователь может
        добавлять комментарии.
        """
        self.auth_client.post(
            reverse('posts:add_comment', args=[self.newpost.pk]),
            {'text': 'test comment text'}
        )
        response = self.auth_client.get(
            reverse('posts:post_detail', args=[self.newpost.pk])
        )
        self.assertEqual(len(response.context['comments']), 1)
        self.assertTrue(
            Comment.objects.filter(
                text='test comment text',
                author=self.user_author,
                post=self.newpost,
            ).exists()
        )

    def test_add_comment_check_guest(self):
        """
        Проверка, что неавторизированный пользователь не может
        добавлять комментарии.
        """
        guest_client = Client()
        guest_client.post(
            reverse('posts:add_comment', args=[self.newpost.pk]),
            {'text': 'test comment'}
        )
        response = guest_client.get(
            reverse('posts:post_detail', args=[self.newpost.pk])
        )
        self.assertEqual(len(response.context['comments']), 0)

    def follow_page_context(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан.
        """
        Follow.objects.create(
            user=self.user_not_author,
            author=self.user_author
        )
        self.auth_not_author.get(
            reverse(
                'posts:profile_follow',
                args=[self.user_author.username]
            )
        )
        response_foll = self.auth_not_author.get(
            reverse('posts:follow_index')
        )
        response_not_foll = self.auth_not_foll.get(
            reverse('posts:follow_index')
        )
        count = Post.objects.filter(author=self.user_author).count()
        if count > NUM_OF_POSTS:
            count = NUM_OF_POSTS
        self.assertEqual(len(response_foll.context['page_obj']), count)
        self.assertEqual(len(response_not_foll.context['page_obj']), 0)

    def test_unfollow_auth(self):
        """
        Проверка, что авторизированный пользователь может удалять
        других пользователей из подписок.
        """
        Follow.objects.create(
            user=self.user_not_author,
            author=self.user_author
        )
        count = Follow.objects.count()
        self.auth_not_author.get(
            reverse(
                'posts:profile_unfollow',
                args=[self.user_author.username]
            )
        )
        self.assertEqual(Follow.objects.count(), count - 1)

    def test_follow_auth(self):
        """
        Проверка, что авторизированный пользователь может подписываться
        на других пользователей.
        """
        count = Follow.objects.count()
        self.auth_not_author.get(
            reverse(
                'posts:profile_follow',
                args=[self.user_author.username]
            )
        )
        self.assertEqual(Follow.objects.count(), count + 1)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Pete')
        cls.auth = Client()
        cls.auth.force_login(cls.user)
        cls.post = Post.objects.create(
            text='great post for testing cache!',
            author=cls.user,
        )

    def test_cash_index_page(self):
        """Тестирование кэша."""
        response_before = self.auth.get(reverse('posts:index'))
        Post.objects.filter(author=self.user).delete()
        response_after = self.auth.get(reverse('posts:index'))
        self.assertEqual(response_after.content, response_before.content)
        cache.clear()
        cache_cleared = self.auth.get(reverse('posts:index'))
        self.assertNotEqual(cache_cleared.content, response_before.content)
