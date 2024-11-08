from rest_framework import serializers
from users.models import Follow
from recipes.models import Tag, Recipe, Ingredient, ShoppingCart, Favorite, IngredientInRecipe
from django.core.files.base import ContentFile
import base64
import os
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import PermissionDenied


User = get_user_model()

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # Извлекаем тип изображения из строки
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            # Генерируем имя для файла
            name = f'temp.{ext}'
            # Декодируем строку base64
            file = ContentFile(base64.b64decode(imgstr), name=name)
            data = file
        return super().to_internal_value(data)

class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя"""

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
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')

class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'avatar'
        )
        read_only_fields = ('id',)

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')

class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),

    )
    amount = serializers.IntegerField()

    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount', 'name', 'measurement_unit')

class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')

class UserWithRecipesSerializer(serializers.ModelSerializer):
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Follow.objects.filter(user=request.user, author=obj).exists()
        return False


class UserAnotherSerializer(UserSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'avatar',
                  'is_subscribed')

class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, attrs):
        # Проверка наличия поля 'avatar' при запросе на обновление
        if 'avatar' not in attrs or attrs['avatar'] is None:
            raise ValidationError({'avatar': 'Необходимо добавить аватар.'})
        return attrs

        

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор моделей ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeMinifiedSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe')

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)

class RecipeSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(many=True)
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

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError('Время приготовления должно быть больше нуля.')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Поле ingredients не должно быть пустым.')
        
        ingredient_ids = []
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError('Количество ингредиента должно быть больше 0.')
            if ingredient['id'] in ingredient_ids:
                raise serializers.ValidationError('Ингредиенты не должны повторяться.')
            ingredient_ids.append(ingredient['id'])

        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Поле tags не должно быть пустым.')

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться.')

        return tags

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if isinstance(request.user, AnonymousUser):
            return False  # Если пользователь не авторизован
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if isinstance(request.user, AnonymousUser):
            return False  # Если пользователь не авторизован
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()

    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags.all(), many=True).data
        return representation
    
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tag_ids = validated_data.pop('tags')

        user = self.context.get('request').user
        if isinstance(user, AnonymousUser):
            raise serializers.ValidationError("You must be logged in to create a recipe.")
        recipe = Recipe.objects.create(author=user, **validated_data)

        # Устанавливаем теги через их ID
        recipe.tags.set(tag_ids)

        for ingredient_data in ingredients_data:
            ingredient_obj = ingredient_data['id']  # Теперь это объект, закодированный как ID
            amount = ingredient_data['amount']
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                amount=amount
            )

        return recipe

    def update(self, instance, validated_data):
        if instance.author != self.context.get('request').user:
            raise PermissionDenied("Только автор рецепта может его обновить.")
        ingredients_data = validated_data.pop('ingredients', [])
        tag_ids = validated_data.pop('tags', [])

        if not ingredients_data:
            raise serializers.ValidationError('Поле ingredients не должно быть пустым.')
        if not tag_ids:
            raise serializers.ValidationError('Поле tags не должно быть пустым.')

        # Очистка старых ингредиентов и тегов
        instance.ingredients.clear()
        instance.tags.clear()

        # Устанавливаем теги через их ID
        instance.tags.set(tag_ids)

        for ingredient_data in ingredients_data:
            ingredient_obj = ingredient_data['id']  # Теперь это объект, закодированны как ID
            amount = ingredient_data['amount']
            IngredientInRecipe.objects.create(
                recipe=instance,
                ingredient=ingredient_obj,
                amount=amount
            )

        return super().update(instance, validated_data)