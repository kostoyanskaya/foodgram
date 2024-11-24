from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from api.views import LinkViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/users/set_password/', include(
        'djoser.urls'
    ), name='set_password'),
    path('s/<str:short_code>/', LinkViewSet.as_view(
        {'get': 'redirect_short_link'})
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
