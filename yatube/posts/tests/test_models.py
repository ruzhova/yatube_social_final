from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Очень длинный текст, длиннее, чем пятнадцать символов',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Название группы Тест',
            slug='slugtest',
            description='Описание группы Тест',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post_and_group = PostModelTest
        act1 = post_and_group.post.__str__()
        act2 = post_and_group.group.__str__()
        field_str_expected = {
            act1: post_and_group.post.text[:15],
            act2: post_and_group.group.title,
        }
        for field, expected_value in field_str_expected.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field.__str__(),
                    expected_value
                )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post_and_group = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post_and_group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_texts(self):
        """help_text в полях совпадает с ожидаемым."""
        post_and_group = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post_and_group._meta.get_field(field).help_text,
                    expected_value
                )
