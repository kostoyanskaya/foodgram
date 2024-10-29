from rest_framework import serializers
from users.models import User
from recipes.models import Tag, Recipe, Ingredient

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')

class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор моделей ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'image',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'ingredients'
        )