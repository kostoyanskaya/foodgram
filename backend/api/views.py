from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from users.models import User
from .serializers import UserSerializer
from rest_framework.response import Response
from recipes.models import Tag, Recipe, Ingredient
from .serializers import TagSerializer, RecipeSerializer, IngredientSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .filters import RecipeFilter, IngredientFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrReadOnly

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с объектами модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']

    def retrieve(self, request, *args, **kwargs):
        """Метод получения тега по ID."""
        tag = get_object_or_404(Tag, id=kwargs['pk'])
        serializer = self.get_serializer(tag)
        return Response(serializer.data)
    
class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с объектами модели Ingredient."""
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_object(self):
        """Получаем рецепт по ID из параметров URL."""
        return get_object_or_404(Recipe, id=self.kwargs['id'])
    
    def perform_create(self, serializer):
        """Создание нового рецепта."""
        serializer.save(author=self.request.user)
