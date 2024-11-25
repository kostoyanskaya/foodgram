import random
import string

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from users.models import User
from django.core.exceptions import ValidationError


class Tag(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=32, unique=True, blank=True, null=True, verbose_name='Slug'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes', verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    name = models.CharField(max_length=256, verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveIntegerField(validators=(
        MinValueValidator(1, message='Время должно быть больше 0'),
        MaxValueValidator(1000, message='Время должно быть больше 0'),
    ), verbose_name='Время приготовления')
    image = models.ImageField(upload_to='recipes/', verbose_name='Изображение')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    short_code = models.CharField(
        max_length=10, editable=False, unique=True, blank=True
    )

    def __str__(self):
        return self.name

    def generate_short_code(self, length=6):
        """Генерирует уникальный короткий код."""
        letters = string.ascii_letters + string.digits
        short_code = ''.join(random.choice(letters) for _ in range(length))
        return short_code

    def clean(self):
        super().clean()
        if not hasattr(self, 'pk') and not self.ingredients.exists():
            raise ValidationError(
                {'ingredients': ['Нужно добавить хотя бы один ингредиент']}
            )

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

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
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, "Количество должно быть больше 1")
        ],
        verbose_name='Количество'
    )

    class Meta:
        default_related_name = 'ingredient_recipe'
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
