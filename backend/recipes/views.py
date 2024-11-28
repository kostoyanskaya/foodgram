from django.shortcuts import get_object_or_404, redirect
from .models import Recipe


def redirect_short_link(request, short_code=None):
    """Получаем рецепт по короткому коду."""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(f'/recipes/{recipe.id}')
