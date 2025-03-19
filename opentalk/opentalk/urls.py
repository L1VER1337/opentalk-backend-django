"""
URL configuration for opentalk project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

from users.views import UserViewSet, RegisterView, ChangePasswordView, UpdateStatusView, LogoutView
from posts.views import PostViewSet, CommentViewSet, HashtagViewSet, TrendViewSet
# from messages_api.views import ChatViewSet, MessageViewSet
# from notifications.views import NotificationViewSet, PremiumViewSet

# Создаем автоматический роутер для API
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'hashtags', HashtagViewSet)
router.register(r'trends', TrendViewSet)
# router.register(r'chats', ChatViewSet, basename='chat')
# router.register(r'messages', MessageViewSet, basename='message')
# router.register(r'notifications', NotificationViewSet, basename='notification')
# router.register(r'premium', PremiumViewSet, basename='premium')

# Схема API для Swagger/Redoc
schema_view = get_schema_view(
    openapi.Info(
        title="OpenTalk API",
        default_version='v1',
        description="API для социальной сети OpenTalk",
        contact=openapi.Contact(email="admin@opentalk.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API эндпоинты
    path('api/', include(router.urls)),
    
    # Аутентификация
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', TokenObtainPairView.as_view(permission_classes=[AllowAny]), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(permission_classes=[AllowAny]), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(permission_classes=[AllowAny]), name='token_verify'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Пользовательские эндпоинты
    path('api/users/update_status/', UpdateStatusView.as_view(), name='update_status'),
    
    # Документация API
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Добавляем URL для статических и медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
