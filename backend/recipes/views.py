from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def redirect_short_link(request, pk=None):
    """Проверяем существование рецепта по id и выполняем редирект."""
    if not Recipe.objects.filter(id=pk).exists():
        raise Http404("Рецепт не найден")
    return redirect(f'/recipes/{pk}/')
