from django.urls import path, include
from rest_framework import routers
from .views import UserViewSet, TagViewSet, RecipeViewSet, IngredientViewSet, ShoppingCartViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'shopping_cart', ShoppingCartViewSet, basename='shopping_cart')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]