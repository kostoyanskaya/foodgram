from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
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
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeMinifiedSerializer,
    RecipeSerializer, TagSerializer, UserDetailSerializer,
    UserRegistrationSerializer, UserWithRecipesSerializer
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow

SITE_URL = 'http://foodgramdelicious.ddnsking.com'

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Работа с пользователями."""
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        elif request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(
                {'Аватар удален.'}, status=status.HTTP_204_NO_CONTENT
            )

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
        user = request.user
        following = Follow.objects.filter(user=user).select_related('author')
        authors = [follow.author for follow in following]

        results = []
        recipes_limit = request.query_params.get('recipes_limit', None)

        for author in authors:
            recipes = Recipe.objects.filter(author=author)
            if recipes_limit is not None:
                recipes = recipes[:int(recipes_limit)]

            recipes_count = recipes.count()
            recipes_data = RecipeMinifiedSerializer(
                recipes, many=True, context={'request': request}
            ).data

            response_data = UserWithRecipesSerializer(
                author, context={'request': request}
            ).data
            response_data['recipes_count'] = recipes_count
            response_data['recipes'] = recipes_data

            results.append(response_data)

        page = self.paginate_queryset(results)

        if page is not None:
            return self.get_paginated_response(page)

        return Response({'count': len(results), 'results': results})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)

        if author == request.user:
            return Response(
                {'Cannot subscribe.'}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            follow, created = Follow.objects.get_or_create(
                user=request.user, author=author
            )
            if created:
                recipes_limit = request.query_params.get('recipes_limit', None)
                recipes = Recipe.objects.filter(author=author)
                if recipes_limit is not None:
                    recipes = recipes[:int(recipes_limit)]

                recipes_count = recipes.count()
                recipes_data = RecipeMinifiedSerializer(
                    recipes, many=True, context={'request': request}
                ).data

                response_data = UserWithRecipesSerializer(
                    author, context={'request': request}
                ).data
                response_data['recipes_count'] = recipes_count
                response_data['recipes'] = recipes_data

                return Response(
                    response_data, status=status.HTTP_201_CREATED
                )

            return Response(
                {'Уже подписан.'}, status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            follow = Follow.objects.filter(
                user=request.user, author=author
            ).first()
            if follow:
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'Subscription not found.'}, status=status.HTTP_400_BAD_REQUEST
            )


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с объектами модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get']

    def get_object(self):
        """Получаем тег по ID из параметров URL."""
        return get_object_or_404(Tag, id=self.kwargs['pk'])


class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с объектами модели Ingredient."""
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None

    def get_object(self):
        """Получаем тег по ID из параметров URL."""
        return get_object_or_404(Ingredient, id=self.kwargs['pk'])


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с объектами модели Recipe."""
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination

    def get_object(self):
        """Получаем тег по ID из параметров URL."""
        return get_object_or_404(Recipe, id=self.kwargs['pk'])

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'У вас нет прав.'}, status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            if not Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                serializer = RecipeMinifiedSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                {'Рецепт уже в избранном.'}, status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).first()
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'Рецепт не найден.'}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_link(self, request, pk):
        """Получаем короткую ссылку."""
        get_object_or_404(Recipe, id=pk)
        return Response(
            {'short-link': f'{SITE_URL}/recipes/{pk}'},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = RecipeMinifiedSerializer(recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                {'Рецепт уже добавлен'}, status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            shopping_cart = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).first()
            if shopping_cart:
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'Не найден.'}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).all()
        ingredients_count = {}
        for item in shopping_cart:
            ingredients = item.recipe.ingredients.all()
            for ingredient_in_recipe in ingredients:
                ingredient_id = ingredient_in_recipe.id
                ingredient_name = ingredient_in_recipe.name
                ingredient_amount = ingredient_in_recipe.amount
                if ingredient_id in ingredients_count:
                    ingredients_count[ingredient_id]['amount'] += (
                        ingredient_amount
                    )
                else:
                    ingredients_count[ingredient_id] = {
                        'name': ingredient_name,
                        'amount': ingredient_amount
                    }
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        response.write("Shopping Cart:\\n")
        for ingredient in ingredients_count.values():
            response.write(f"{ingredient['name']}: {ingredient['amount']}\\n")

        return response
