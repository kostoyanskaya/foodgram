from django.shortcuts import get_object_or_404, redirect
from .models import Recipe


def redirect_short_link(request, pk=None):
    """Получаем рецепт по id."""
    recipe = get_object_or_404(Recipe, id=pk)
    return redirect(f'/recipes/{recipe.id}/')
