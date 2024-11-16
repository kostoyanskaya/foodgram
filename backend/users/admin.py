from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    list_display_links = ('name',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author').prefetch_related(
            'tags',
            'ingredients'
        )

    def author(self, obj):
        return obj.author.username

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'Количество в избранном'

    def ingredients_list(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()]
        )
    ingredients_list.short_description = 'Ингредиенты'

    def tags_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    tags_list.short_description = 'Теги'

    list_display += ('tags_list', 'ingredients_list')


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
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
