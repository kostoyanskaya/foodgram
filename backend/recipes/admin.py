from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import mark_safe

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)

admin.site.unregister(Group)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    min_num = 1
    extra = 0
    fields = ('ingredient', 'amount', 'measurement_unit_display')
    readonly_fields = ('measurement_unit_display',)

    @admin.display(description='Единица измерения')
    def measurement_unit_display(self, ingredient_in_recipe):
        return ingredient_in_recipe.ingredient.measurement_unit


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author',
        'tags_list', 'favorites_count', 'product_list',
        'show_image'
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'tags')
    inlines = [IngredientInRecipeInline]

    @admin.display(description='Изображение')
    @mark_safe
    def show_image(self, recipe):
        if recipe.image:
            return (
                f'<img src=\'{recipe.image.url}\' '
                'width=\'50\' height=\'50\' />'
            )
        return 'Нет изображения'

    @admin.display(description='Избранное')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Теги')
    @mark_safe
    def tags_list(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Продукты')
    @mark_safe
    def product_list(self, recipe):
        return '<br>'.join(
            f'{ingredient.ingredient.name} '
            f'({ingredient.amount} {ingredient.ingredient.measurement_unit})'
            for ingredient in recipe.ingredients_in_recipes.all()
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    list_display_links = ('name',)
    search_fields = ('name',)

    @admin.display(description='Рецепты')
    def recipe_count(self, tag):
        return tag.recipes.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name', 'measurement_unit',)

    @admin.display(description='Рецепты')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
