from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    TagSerializer,
    UserDetailSerializer,
    UserWithRecipesSerializer
)
from .utils import format_shopping_list
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Follow


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
            user.avatar.delete()
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
            authors__user=request.user
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
            if request.user == author:
                raise ValidationError(
                    'Вы не можете подписаться на самого себя.'
                )
            _, created = Follow.objects.get_or_create(
                author=author, user=request.user
            )
            if not created:
                raise ValidationError(
                    'Вы уже подписаны на этого пользователя.'
                )
            user_serializer = UserWithRecipesSerializer(
                author,
                context={'request': request}
            )
            user_data = user_serializer.data
            user_data['recipes'] = user_serializer.get_recipes(author)
            return Response(user_data, status=status.HTTP_201_CREATED)

        follow = get_object_or_404(Follow, author=author, user=request.user)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def handle_cart_or_favorite(request, model, recipe):
        """Обработчик для добавления/удаления в избранное или корзину"""
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = RecipeMinifiedSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            raise ValidationError('Рецепт уже добавлен.')

        elif request.method == 'DELETE':
            instance = get_object_or_404(
                model, user=request.user, recipe=recipe
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(f"Рецепт с id {pk} не найден.")

        short_link = request.build_absolute_uri(
            reverse('redirect_short_link', args=[pk])
        )
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
            'recipe__ingredients_in_recipes'
        ).annotate(
            ingredient_name=F(
                'recipe__ingredients_in_recipes__ingredient__name'
            ),
            ingredient_unit=F(
                'recipe__ingredients_in_recipes__ingredient__measurement_unit'
            ),
            amount=F('recipe__ingredients_in_recipes__amount'),
        ).values(
            'ingredient_name',
            'ingredient_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient_name')
        recipe_ids = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe_id', flat=True).distinct()
        recipes = set(Recipe.objects.filter(
            id__in=recipe_ids
        ).values_list(
            'name', flat=True
        ))
        shopping_list = format_shopping_list(cart, recipes)
        response = FileResponse(
            shopping_list,
            as_attachment=True,
            filename='shopping_cart.txt'
        )

        return response
