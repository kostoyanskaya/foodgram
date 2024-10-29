from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    username = models.CharField(
        'Username',
        unique=True,
        blank=False,
        max_length=150,
        validators=[RegexValidator(r'^[\w.@+-]+$')]
    )
    email = models.EmailField(
        'E-mail address',
        unique=True,
        blank=False
    )
    first_name = models.CharField(
        'First name',
        max_length=150,
        blank=True
    )
    last_name = models.CharField(
        'Last name',
        max_length=150,
        blank=True
    )