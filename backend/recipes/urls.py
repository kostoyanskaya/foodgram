from django.urls import path
from .views import redirect_short_link

urlpatterns = [
    path(
        's/<int:pk>/',
        redirect_short_link,
        name='redirect_short_link'
    ),
]
