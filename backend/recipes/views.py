from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from .models import Recipe


def redirect_short_link(request, pk=None):
    """Проверяем существование рецепта по id и выполняем редирект."""
    if not Recipe.objects.filter(id=pk).exists():
        raise ValidationError(f"Рецепт с id {pk} не найден.")
    return redirect(f'/recipes/{pk}/')
