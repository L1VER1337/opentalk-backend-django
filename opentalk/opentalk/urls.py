"""
URL configuration for opentalk project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from users.views import (
    UserViewSet, RegisterView, ChangePasswordView, UpdateStatusView, LogoutView, OnlineStatusView,
    SendVerificationCodeView, VerifyCodeView, PhoneLoginView, CreateUserByPhoneView, CheckUsernameView,
    QRCodeView, QRStatusView, AuthenticateByQRView
)
from posts.views import PostViewSet, CommentViewSet, HashtagViewSet, TrendViewSet
from messages_api.views import ChatViewSet, MessageViewSet, AttachmentViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'hashtags', HashtagViewSet, basename='hashtag')
router.register(r'trends', TrendViewSet, basename='trend')
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'attachments', AttachmentViewSet, basename='attachment')

schema_view = get_schema_view(
   openapi.Info(
      title="OpenTalk API",
      default_version='v1',
      description="API для социальной сети OpenTalk",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@opentalk.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # Маршруты для работы с пользователями
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/update-status/', UpdateStatusView.as_view(), name='update_status'),
    path('api/online-status/', OnlineStatusView.as_view(), name='online_status'),
    # Маршруты для авторизации по телефону
    path('api/send-verification-code/', SendVerificationCodeView.as_view(), name='send_verification_code'),
    path('api/verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('api/phone-login/', PhoneLoginView.as_view(), name='phone_login'),
    path('api/create-user-by-phone/', CreateUserByPhoneView.as_view(), name='create_user_by_phone'),
    path('api/check-username/', CheckUsernameView.as_view(), name='check_username'),
    
    # Альтернативные пути для соответствия документации
    path('api/auth/send-code', SendVerificationCodeView.as_view(), name='send_code'),
    path('api/auth/verify-code', VerifyCodeView.as_view(), name='verify_code_alt'),
    path('api/auth/check-username', CheckUsernameView.as_view(), name='check_username_alt'),
    path('api/auth/register', CreateUserByPhoneView.as_view(), name='register'),
    path('api/auth/login', PhoneLoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/qr-code', QRCodeView.as_view(), name='qr-code'),
    path('api/auth/check-qr-status', QRStatusView.as_view(), name='check-qr-status'),
    path('api/auth/authenticate-qr', AuthenticateByQRView.as_view(), name='authenticate-qr'),
    
    # Пути без префикса 'api' (для совместимости с фронтендом)
    path('auth/send-code', SendVerificationCodeView.as_view(), name='send_code_no_prefix'),
    path('auth/verify-code', VerifyCodeView.as_view(), name='verify_code_no_prefix'),
    path('auth/check-username', CheckUsernameView.as_view(), name='check_username_no_prefix'),
    path('auth/register', CreateUserByPhoneView.as_view(), name='register_by_phone_no_prefix'),
    path('auth/logout', LogoutView.as_view(), name='logout_no_prefix'),
    path('auth/refresh-token', TokenRefreshView.as_view(), name='token_refresh_no_prefix'),
    
    # Документация API
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Добавление URL для статических и медиа файлов только в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
