from django.db import models
from django.contrib.auth.models import AbstractUser
from .validators import validate_username


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Логин',
        unique=True,
        blank=False,
        max_length=150,
        validators=[validate_username]
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        blank=False,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False
    )
    is_subscribed = models.BooleanField(
        verbose_name='Подписка',
        default=False
    )
    avatar = models.ImageField(
        upload_to='users/',
        verbose_name='Аватар',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Кто подписан',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='На кого подписан',
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
