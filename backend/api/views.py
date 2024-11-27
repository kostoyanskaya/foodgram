from collections import defaultdict
import os

from django.contrib.auth import get_user_model
from django.db.models import F
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeMinifiedSerializer,
    RecipeSerializer, TagSerializer, UserDetailSerializer,
    UserWithRecipesSerializer
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow

SITE_URL = 'foodgramdelicious.ddnsking.com'

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Работа с пользователями."""
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def manage_avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if user.avatar:
            avatar_file_path = user.avatar.path
            if os.path.exists(avatar_file_path):
                os.remove(avatar_file_path)
        user.avatar = None
        user.save()
        return Response({'Аватар удален.'}, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes')

        page = self.paginate_queryset(queryset)

        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request}
        )

        user_data = serializer.data

        for index, user in enumerate(user_data):
            user_instance = User.objects.get(pk=user['id'])
            user_data[index]['recipes'] = serializer.child.get_recipes(
                user_instance
            )
        return self.get_paginated_response(user_data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            if request.user.id == author.id:
                raise ValidationError(
                    {'Вы не можете подписаться на самого себя'}
                )

            if Follow.objects.filter(
                author=author, user=request.user
            ).exists():
                raise ValidationError(
                    {'Вы уже подписаны на этого пользователя.'}
                )
            Follow.objects.create(
                author=author,
                user=request.user
            )

            user_serializer = UserWithRecipesSerializer(
                author,
                context={'request': request}
            )

            user_data = user_serializer.data
            user_data['recipes'] = user_serializer.get_recipes(author)

            return Response(user_data, status=status.HTTP_201_CREATED)
        try:
            follow = Follow.objects.get(author=author, user=request.user)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            raise ValidationError({'Подписка не найдена.'})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с объектами модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с объектами модели Ingredient."""
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с объектами модели Recipe"""
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination

    @staticmethod
    def handle_cart_or_favorite(request, model, recipe):
        """Обработчик для добавления/удаления в избранное или корзину"""
        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = RecipeMinifiedSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                {'Рецепт уже добавлен.'}, status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            instance = model.objects.filter(
                user=request.user, recipe=recipe
            ).first()
            if instance:
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'Не найден.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self.handle_cart_or_favorite(request, Favorite, recipe)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self.handle_cart_or_favorite(request, ShoppingCart, recipe)

    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_link(self, request, pk):
        """Получаем короткую ссылку."""
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = request.build_absolute_uri(f'/s/{recipe.short_code}/')
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        cart = ShoppingCart.objects.filter(user=request.user).prefetch_related(
            'recipe__ingredient_recipe'
        ).annotate(
            ingredient_name=F('recipe__ingredient_recipe__ingredient__name'),
            ingredient_unit=F(
                'recipe__ingredient_recipe__ingredient__measurement_unit'
            ),
            amount=F('recipe__ingredient_recipe__amount'),
        ).values(
            'ingredient_name',
            'ingredient_unit',
            'amount'
        )

        ingredients_summary = defaultdict(int)
        for ingredient in cart:
            ingredients_summary[
                (ingredient['ingredient_name'], ingredient['ingredient_unit'])
            ] += ingredient['amount']

        ingredients_info = [
            f'{name.capitalize()} - {amount} ({unit})'
            for (name, unit), amount in ingredients_summary.items()
        ]

        shopping_list = '\\\\n'.join([
            'Список ингредиентов:',
            *ingredients_info,
            'Перечень рецептов:',
            *[f'Рецепт: {recipe.name}' for recipe in Recipe.objects.filter(
                shoppingcart__user=request.user
            )]
        ])

        return FileResponse(
            shopping_list.encode('utf-8'),
            content_type='text/plain; charset=utf-8',
            headers={
                'Content-Disposition': (
                    'attachment; filename="shopping_cart.txt"'
                )
            }
        )


class LinkViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def redirect_short_link(self, request, short_code=None):
        """Получаем рецепт по короткому коду."""
        recipe = get_object_or_404(Recipe, short_code=short_code)

        return HttpResponseRedirect(
            request.build_absolute_uri(f'/recipes/{recipe.id}')
        )
