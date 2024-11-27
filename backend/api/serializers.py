import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from .constants import MIN_AMOUNT
from .validators import validate_ingredients, validate_tags
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Follow


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Поле для работы с изображениями в формате base64.
    Преобразует строку base64 в файловый объект.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name = f'temp.{ext}'
            file = ContentFile(base64.b64decode(imgstr), name=name)
            data = file
        return super().to_internal_value(data)


class UserDetailSerializer(BaseUserSerializer):
    """Сериализатор для получения информации о пользователе"""
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = list(
            BaseUserSerializer.Meta.fields
        ) + ['avatar', 'is_subscribed']

    def get_is_subscribed(self, user_instance):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=user_instance
            ).exists()
        return False


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientInRecipe."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        error_messages={
            'min_value': f"Количество ингредиента должно быть больше "
                         f"{MIN_AMOUNT}"
        }
    )

    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount', 'name', 'measurement_unit')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Уменьшенная версия сериализатора для модели Recipe."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, attrs):
        if 'avatar' not in attrs or attrs['avatar'] is None:
            raise ValidationError({'avatar': 'Необходимо добавить аватар.'})
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор моделей ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
    author = UserDetailSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredient_recipe'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def validate_tags(self, tag_values):
        return validate_tags(tag_values)

    def validate_ingredients(self, ingredients_value):
        return validate_ingredients(ingredients_value)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        return representation

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredient_recipe')
        self.validate_ingredients(ingredients_data)

        tags_data = validated_data.pop('tags')
        user = self.context.get('request').user

        if isinstance(user, AnonymousUser):
            raise serializers.ValidationError(
                "Вы должны войти в систему, чтобы создать рецепт"
            )
        validated_data['author'] = user

        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)

        self._bulk_create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        if instance.author != self.context.get('request').user:
            raise PermissionDenied("Только автор рецепта может его обновить.")
        ingredients_data = validated_data.pop('ingredient_recipe', [])
        tags_data = validated_data.pop('tags', [])

        self.validate_ingredients(ingredients_data)
        if not tags_data:
            raise serializers.ValidationError(
                "Поле tags не должно быть пустым."
            )
        instance.tags.clear()
        instance.tags.set(tags_data)
        IngredientInRecipe.objects.filter(recipe=instance).delete()

        self._bulk_create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def _bulk_create_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )


class UserWithRecipesSerializer(BaseUserSerializer):
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = list(
            BaseUserSerializer.Meta.fields
        ) + ['avatar', 'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False

    def get_recipes(self, user):
        recipes = user.recipes.all()
        recipes_limit = self.context.get('request').GET.get(
            'recipes_limit', None
        )

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    recipes_limit = 0
            except ValueError:
                recipes_limit = recipes.count()
        else:
            recipes_limit = recipes.count()

        recipes = recipes[:recipes_limit]
        serializer = RecipeMinifiedSerializer(recipes, many=True)
        return serializer.data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['recipes_count'] = instance.recipes.count()
        return representation
