from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import mark_safe

from .models import Follow, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'show_avatar',
        'get_recipes_count',
        'get_subscriptions_count',
        'get_followers_count',
    )
    search_fields = ('username', 'email')

    @admin.display(description='ФИО')
    def full_name(self, user):
        """Возвращает ФИО пользователя."""
        return f'{user.first_name} {user.last_name}'

    @mark_safe
    def show_avatar(self, user):
        """Возвращает HTML-разметку аватара."""
        if user.avatar:
            return (
                f'<img src=\'{user.avatar.url}\' '
                f'width=\'50\' height=\'50\' />'
            )
        return 'Нет аватара'

    @admin.display(description='Рецепты')
    def get_recipes_count(self, user):
        """Возвращает количество рецептов пользователя."""
        return user.recipes.count()

    @admin.display(description='Подписки')
    def get_subscriptions_count(self, user):
        """Возвращает количество подписок."""
        return user.authors.count()

    @admin.display(description='Подписчики')
    def get_followers_count(self, user):
        """Возвращает количество подписчиков."""
        return user.followers.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
