import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if value == 'me':
        raise ValidationError('The username "me" is not allowed.')

    pattern = r'[\w.@+-]+\Z'
    if not re.match(pattern, value):
        raise ValidationError('Username can not be with such simbols.')
