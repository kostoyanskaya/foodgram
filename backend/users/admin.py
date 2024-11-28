from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import mark_safe

from .models import User, Follow


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

    def full_name(self, obj):
        """Возвращает ФИО пользователя."""
        return f"{obj.first_name} {obj.last_name}"

    full_name.short_description = 'ФИО'

    @mark_safe
    def show_avatar(self, obj):
        """Возвращает HTML-разметку аватара."""
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" width="50" height="50" />'
        return 'Нет аватара'

    show_avatar.short_description = 'Аватар'

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов пользователя."""
        return obj.recipes.count()

    get_recipes_count.short_description = 'Количество рецептов'

    def get_subscriptions_count(self, obj):
        """Возвращает количество подписок."""
        return obj.followings.count()

    get_subscriptions_count.short_description = 'Количество подписок'

    def get_followers_count(self, obj):
        """Возвращает количество подписчиков."""
        return obj.followers.count()

    get_followers_count.short_description = 'Количество подписчиков'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
