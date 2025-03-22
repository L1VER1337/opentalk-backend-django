from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Subscription, VerificationCode

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    """Кастомный админ-класс для модели пользователя"""
    list_display = ('id', 'username', 'phone', 'email', 'full_name', 'status', 'is_verified')
    list_filter = ('status', 'is_verified', 'is_premium', 'is_staff')
    search_fields = ('username', 'email', 'full_name', 'phone')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('email', 'phone', 'full_name', 'avatar', 'bio')}),
        ('Настройки', {'fields': ('status', 'is_verified', 'is_premium', 'theme_preference')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                  'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )


class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-класс для модели подписок"""
    list_display = ('id', 'follower', 'followed', 'created_at')
    search_fields = ('follower__username', 'followed__username')
    list_filter = ('created_at',)


class VerificationCodeAdmin(admin.ModelAdmin):
    """Админ-класс для модели верификационных кодов"""
    list_display = ('phone', 'code', 'created_at', 'expires_at', 'is_used')
    search_fields = ('phone',)
    list_filter = ('created_at', 'is_used')
    readonly_fields = ('created_at', 'expires_at')


# Регистрация моделей
admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(VerificationCode, VerificationCodeAdmin)
