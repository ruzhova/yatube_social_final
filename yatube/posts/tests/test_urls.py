from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='DwightShroute')
        cls.user_not_author = User.objects.create_user(
            username='AngelaMartin'
        )
        cls.user_group = Group.objects.create(
            title='Название группы Тест',
            slug='slugtest',
        )
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.user)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_not_author)
        cls.post = Post.objects.create(
            text='Очень длинный текст, длиннее, чем 15 символов',
            author=cls.user,
            group=cls.user_group
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.page_not_exist = '/unexisting_page/'
        cls.page_edit = f'/posts/{cls.post.pk}/edit/'

    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template_not_authorized(self):
        """
        URL-адрес использует соответствующий шаблон; неавторизированный
        пользователь.
        """
        for adress, template in self.templates_url_names.items():
            with self.subTest(adress=adress):
                if template != 'posts/create_post.html':
                    response = self.guest_client.get(adress)
                    self.assertTemplateUsed(response, template)

    def test_404_not_authorized(self):
        """
        Неавторизированый пользователь при запросе к несуществующей
        странице видит ошибку 404.
        """
        response = self.guest_client.get(self.page_not_exist)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_302_not_authorized(self):
        """
        Проверка, что неавторизированный пользователь не может создавать
        или редактировать посты и перенаправляется на страницу входа.
        """
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                if template == 'posts/create_post.html':
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(
                        response,
                        f'/auth/login/?next={address}'
                    )

    def test_urls_uses_correct_template_author(self):
        """
        URL-адрес использует соответствующий шаблон; автор поста.
        """
        for adress, template in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client_author.get(adress)
                self.assertTemplateUsed(response, template)

    def test_404_author(self):
        """
        Aвторизированый пользователь при запросе к несуществующей
        странице видит ошибку 404.
        """
        response = self.authorized_client_author.get(self.page_not_exist)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template_authorized_non_author(self):
        """
        URL-адрес использует соответствующий шаблон; авторизированный
        пользователь, не автор.
        """
        for adress, template in self.templates_url_names.items():
            with self.subTest(adress=adress):
                if adress != f'/posts/{self.post.pk}/edit/':
                    response = self.authorized_client.get(adress)
                    self.assertTemplateUsed(response, template)

    def test_302_non_author(self):
        """
        Проверка, что пользователь, не являющийся автором поста, не может
        его редактировать и перенаправляется на страницу поста.
        """
        response = self.authorized_client.get(self.page_edit)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
