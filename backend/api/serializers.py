import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

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


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    """Сериализатор для получения информации о пользователе"""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Follow.
    """
    class Meta:
        model = Follow
        fields = ('user', 'author')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientInRecipe."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    amount = serializers.IntegerField()

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


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


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


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""
    recipe = RecipeMinifiedSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe')

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)


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
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

        extra_kwargs = {
            'ingredients': {'required': True, 'allow_empty': False},
            'tags': {'required': True, 'allow_empty': False},
        }

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if isinstance(request.user, AnonymousUser):
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if isinstance(
            request.user, AnonymousUser
        ):
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        return representation

    def validate_tags(self, value):
        return validate_tags(value)

    def validate_ingredients(self, value):
        return validate_ingredients(value)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredient_recipe')
        tags_data = validated_data.pop('tags')
        user = self.context.get('request').user

        if isinstance(user, AnonymousUser):
            raise serializers.ValidationError(
                "Вы должны войти в систему, чтобы создать рецепт."
            )

        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags_data)

        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )

        return recipe

    def update(self, instance, validated_data):
        if instance.author != self.context.get('request').user:
            raise PermissionDenied("Только автор рецепта может его обновить.")
        ingredients_data = validated_data.pop('ingredient_recipe', [])
        tags_data = validated_data.pop('tags', [])

        if not ingredients_data:
            raise serializers.ValidationError(
                "Поле ingredients не должно быть пустым."
            )
        if not tags_data:
            raise serializers.ValidationError(
                "Поле tags не должно быть пустым."
            )
        instance.tags.clear()
        instance.tags.set(tags_data)

        for ingredient in ingredients_data:
            IngredientInRecipe.objects.filter(
                recipe=instance,
                ingredient=ingredient['ingredient']['id']
            ).delete()
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                recipe=instance,
                ingredient=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )
        instance.save()

        return super().update(instance, validated_data)
