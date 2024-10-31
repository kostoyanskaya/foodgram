from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from users.models import User, Follow
from .serializers import UserSerializer
from rest_framework.response import Response
from recipes.models import Tag, Recipe, Ingredient, Favorite
from .serializers import TagSerializer, RecipeSerializer, IngredientSerializer, AvatarSerializer, ChangePasswordSerializer, UserWithRecipesSerializer
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
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

class CustomTokenObtainView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'auth_token': token.key}, status=status.HTTP_200_OK)

        return Response({'error': 'Неверные учетные данные!'}, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def avatar(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Получаем изображение и сохраняем его
        avatar_data = serializer.validated_data.get('avatar')
        if avatar_data:
            format, imgstr = avatar_data.split(';base64,')  
            ext = format.split('/')[-1]  
            avatar_file = ContentFile(base64.b64decode(imgstr), name=f'avatar.{ext}')

            # Сохраняем файл пользователя
            user = request.user
            user.avatar.save(f'avatar.{ext}', avatar_file)
            user.save()

        return Response({'avatar': user.avatar.url}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:  # Если у пользователя есть аватар
            user.avatar.delete(save=False)  # Удаляем файл
            user.avatar = None  # Обнуляем поле аватара
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Аватар не найден.'}, status=status.HTTP_404_NOT_FOUND)

    # Ваш существующий метод `me`
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')

        # Проверка текущего пароля
        if not user.check_password(current_password):
            return Response({'current_password': ['Неверный пароль.']}, status=status.HTTP_400_BAD_REQUEST)

        # Установка нового пароля
        user.set_password(new_password)
        user.save()

        # Обновление сессии пользователя
        update_session_auth_hash(request, user)

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        following = Follow.objects.filter(user=user).select_related('author')
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            following, many=True, context={'request': request}
        )
        return Response({'count': following.count(), 'results': serializer.data})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author == request.user:
            return Response({'error': 'Cannot subscribe to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(user=request.user, author=author)
        if created:
            return Response(UserWithRecipesSerializer(author, context={'request': request}).data, status=status.HTTP_201_CREATED)

        return Response({'error': 'Already subscribed.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        follow = get_object_or_404(Follow, user=request.user, author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



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

    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            favorite = Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeSerializer(favorite.recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['delete'], detail=True, permission_classes=[IsAuthenticated])
    def unfavorite(self, request, pk=None):
        recipe = self.get_object()
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe).first()
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Рецепт не найден в избранном'}, status=status.HTTP_400_BAD_REQUEST)
