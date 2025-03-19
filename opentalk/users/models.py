from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Расширенная модель пользователя с дополнительными полями профиля
    """
    STATUS_CHOICES = (
        ('online', 'Онлайн'),
        ('offline', 'Офлайн'),
        ('dnd', 'Не беспокоить'),
    )
    
    THEME_CHOICES = (
        ('light', 'Светлая'),
        ('dark', 'Темная'),
    )
    
    # Дополнительные поля профиля
    full_name = models.CharField(_("Полное имя"), max_length=255, blank=True)
    avatar = models.ImageField(_("Аватар"), upload_to='avatars/', null=True, blank=True, max_length=500)
    bio = models.TextField(_("О себе"), blank=True)
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES, default='offline')
    location = models.CharField(_("Местоположение"), max_length=100, blank=True)
    last_login = models.DateTimeField(_("Последний вход"), null=True, blank=True)
    created_at = models.DateTimeField(_("Дата регистрации"), auto_now_add=True)
    is_premium = models.BooleanField(_("Премиум-статус"), default=False)
    is_verified = models.BooleanField(_("Верификация"), default=False)
    theme_preference = models.CharField(_("Тема оформления"), max_length=10, choices=THEME_CHOICES, default='light')
    
    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
    
    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель подписки между пользователями (подписчики/подписки)
    """
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following',
        verbose_name=_("Подписчик")
    )
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers',
        verbose_name=_("Подписка")
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Подписка")
        verbose_name_plural = _("Подписки")
        unique_together = ('follower', 'followed')  # Пользователь может подписаться на другого только один раз
    
    def __str__(self):
        return f"{self.follower.username} -> {self.followed.username}"
