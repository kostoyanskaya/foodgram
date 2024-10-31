from django.urls import path, include
from rest_framework import routers
from .views import UserViewSet, TagViewSet, RecipeViewSet, IngredientViewSet, CustomTokenObtainView, CustomTokenLogoutView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('', include(router.urls)),
    path('api/auth/token/login/', CustomTokenObtainView.as_view(), name='token_login'),
    path('api/auth/token/logout/', CustomTokenLogoutView.as_view(), name='token_logout'),
]