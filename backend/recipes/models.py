from django.db import models
from users.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=32, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


    
class Recipe(models.Model): 
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes',
        blank=False,
    )
    name = models.CharField(max_length=256)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(validators=(
            MinValueValidator(1, message='Одна минута'),
            MaxValueValidator(1440, message='1440 минут'),
        ))
    image = models.ImageField(upload_to='recipes/')
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name
    
class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')
    
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
    
class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент в рецепте',
    )
    amount = models.PositiveSmallIntegerField()