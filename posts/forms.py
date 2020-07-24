from django import forms
from . import models


class PostForm(forms.ModelForm):
    class Meta:
        model = models.Post
        fields = ["group", "text", 'image']

        help_texts = {
            "group": ("Группа. Не обязательное поле"),
            "text": ("Введите текст поста"),
        }

        labels = {
            'text': 'Текст',
            'group': 'Группа'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ["text"]

        help_texts = {
            "text": ("Комментарий"),
        }

        labels = {
            "text": "Текст"
        }

        widgets = {
            'text': forms.Textarea(attrs={'cols': 40, 'rows': 10}),
        }