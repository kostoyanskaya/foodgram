from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from users.models import Follow
from rest_framework.response import Response
from recipes.models import Tag, Recipe, Ingredient, Favorite, ShoppingCart, IngredientInRecipe
from .serializers import TagSerializer, RecipeSerializer, UserDetailSerializer, IngredientSerializer, AvatarSerializer, UserWithRecipesSerializer, ShoppingCartSerializer, RecipeMinifiedSerializer, UserRegistrationSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .filters import RecipeFilter, IngredientFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrReadOnly
from rest_framework.decorators import action
from django.core.files.base import ContentFile
import base64
from django.contrib.auth import update_session_auth_hash
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.pagination import LimitOffsetPagination
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .paginations import LimitPagination 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse

User = get_user_model()



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    pagination_class = LimitPagination
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

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
            return Response({'detail': 'Аватар успешно удален.'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        following = Follow.objects.filter(user=user).select_related('author')

        # Извлекаем авторов из подписок
        authors = [follow.author for follow in following]

        results = []
        recipes_limit = request.query_params.get('recipes_limit', None)

        for author in authors:
            # Получаем все рецепты автора, ограниченные по количеству
            recipes = Recipe.objects.filter(author=author)
            if recipes_limit is not None:
                recipes = recipes[:int(recipes_limit)]

            recipes_count = recipes.count()
            recipes_data = RecipeMinifiedSerializer(recipes, many=True, context={'request': request}).data

            response_data = UserWithRecipesSerializer(author, context={'request': request}).data
            response_data['recipes_count'] = recipes_count
            response_data['recipes'] = recipes_data

            results.append(response_data)

        # Пагинация для results, а не for following
        page = self.paginate_queryset(results)

        if page is not None:
            return self.get_paginated_response(page)

        return Response({'count': len(results), 'results': results})

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        
        if author == request.user:
            return Response({'error': 'Cannot subscribe to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            follow, created = Follow.objects.get_or_create(user=request.user, author=author)
            if created:
                # Получаем все рецепты автора, ограниченные по количеству
                recipes_limit = request.query_params.get('recipes_limit', None)
                recipes = Recipe.objects.filter(author=author)
                if recipes_limit is not None:
                    recipes = recipes[:int(recipes_limit)]

                recipes_count = recipes.count()
                recipes_data = RecipeMinifiedSerializer(recipes, many=True, context={'request': request}).data

                response_data = UserWithRecipesSerializer(author, context={'request': request}).data
                response_data['recipes_count'] = recipes_count
                response_data['recipes'] = recipes_data

                return Response(response_data, status=status.HTTP_201_CREATED)

            return Response({'error': 'Already subscribed.'}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            follow = Follow.objects.filter(user=request.user, author=author).first()
            if follow:
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'Subscription not found.'}, status=status.HTTP_400_BAD_REQUEST)



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
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_object(self):
        """Получаем тег по ID из параметров URL."""
        return get_object_or_404(Recipe, id=self.kwargs['pk'])

    @action(methods=['post', 'delete'], detail=True, permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                serializer = RecipeMinifiedSerializer(recipe, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe).first()
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Рецепт не найден в избранном'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_link(self, request, pk):
        """Получаем короткую ссылку на рецепт по ID."""
        get_object_or_404(Recipe, id=pk)
        return Response(
            {'short-link': f'http://127.0.0.1:8000/recipes/{pk}'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).all()
        ingredients = [item.recipe.name for item in shopping_cart]
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        p.drawString(100, 750, "Shopping Cart:")
        for i, ingredient in enumerate(ingredients):
            p.drawString(100, 730 - (i * 20), ingredient)
        p.showPage()
        p.save()

        return response

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
            if created:
                serializer = RecipeMinifiedSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже добавлен в список покупок'}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            shopping_cart = ShoppingCart.objects.filter(user=request.user, recipe=recipe).first()
            if shopping_cart:
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Рецепт не найден в корзине'}, status=status.HTTP_400_BAD_REQUEST)

