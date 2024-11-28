from django.contrib import admin
from django.utils.html import mark_safe

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author_username',
        'tags_list', 'favorites_count', 'product_list',
        'show_image'
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'tags')
    inlines = [IngredientInRecipeInline]

    def author_username(self, recipe):
        return recipe.author.username
    author_username.short_description = 'Автор'

    @mark_safe
    def show_image(self, recipe):
        if recipe.image:
            return (
                f'<img src=\'{recipe.image.url}\' '
                'width=\'50\' height=\'50\' />'
            )
        return 'Нет изображения'
    show_image.short_description = 'Изображение'

    def favorites_count(self, recipe):
        return recipe.favorite_recipes.count()
    favorites_count.short_description = 'Количество в избранном'

    @mark_safe
    def tags_list(self, recipe):
        return ', '.join(tag.name for tag in recipe.tags.all())
    tags_list.short_description = 'Теги'

    @mark_safe
    def product_list(self, recipe):
        return ', '.join(
            f'{ingredient.ingredient.name} ({ingredient.amount})'
            for ingredient in recipe.ingredients_in_recipes.all()
        )
    product_list.short_description = 'Продукты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    list_filter = ('measurement_unit',)

    def recipes_count(self, ingredient):
        return ingredient.recipes.count()

    recipes_count.short_description = 'Количество рецептов'


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
