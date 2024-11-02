from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re
from django.core.validators import MaxLengthValidator, MinLengthValidator

def validate_username(value):
    if value == 'me':
        raise ValidationError('The username "me" is not allowed.')

    pattern = r'[\w.@+-]+\Z'
    if not re.match(pattern, value):
        raise ValidationError('Username can not be with such simbols.')

class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    username = models.CharField(
        'Username',
        unique=True,
        blank=False,
        max_length=150,
        validators=[validate_username]
    )
    email = models.EmailField(
        'E-mail address',
        unique=True,
        blank=False,
    )
    first_name = models.CharField(
        'first name',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        'last name',
        max_length=150,
        blank=False
    )
    is_subscribed = models.BooleanField(
        'Подписка',
        default=False)
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)


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
        verbose_name = 'подписка'

    def __str__(self):
        return f'{self.user} подписался на {self.author}'