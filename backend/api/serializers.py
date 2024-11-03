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
    ingredient = serializers.SlugRelatedField(
        slug_field='name', 
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('ingredient',)  # Предполагая, что есть поле `amount` в модели IngredientInRecipe

class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')

class UserWithRecipesSerializer(serializers.ModelSerializer):
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

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



class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен быть не менее 8 символов.")
        return value

        

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
    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe')

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)

class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(many=True)

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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False
    
    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False
    
    def get_ingredients(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Ingredient.objects.filter(name=obj).exists()
        return False

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        return recipe
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        return instance