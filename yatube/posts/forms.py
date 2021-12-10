from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def text_check(self):
        if not self.cleaned_data['text']:
            raise forms.ValidationError('Ошибка. Введите текст поста')
        return self.cleaned_data['text']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Введите текст комментария',
        }
