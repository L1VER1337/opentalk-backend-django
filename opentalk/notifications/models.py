from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class Notification(models.Model):
    """
    Модель уведомления для пользователя
    """
    TYPE_CHOICES = (
        ('like', 'Лайк'),
        ('comment', 'Комментарий'),
        ('follow', 'Подписка'),
        ('mention', 'Упоминание'),
        ('message', 'Сообщение'),
        ('repost', 'Репост'),
        ('system', 'Системное'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', 
                           verbose_name=_("Получатель"))
    type = models.CharField(_("Тип"), max_length=20, choices=TYPE_CHOICES)
    content = models.TextField(_("Содержание"))
    reference_id = models.PositiveIntegerField(_("ID объекта"), null=True, blank=True)
    reference_type = models.CharField(_("Тип объекта"), max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    is_read = models.BooleanField(_("Прочитано"), default=False)
    
    class Meta:
        verbose_name = _("Уведомление")
        verbose_name_plural = _("Уведомления")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()} для {self.user.username}"


class PremiumSubscription(models.Model):
    """
    Модель премиум-подписки пользователя
    """
    PLAN_CHOICES = (
        ('monthly', 'Месячный'),
        ('yearly', 'Годовой'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='premium_subscriptions', 
                           verbose_name=_("Пользователь"))
    plan_type = models.CharField(_("Тип плана"), max_length=20, choices=PLAN_CHOICES)
    started_at = models.DateTimeField(_("Дата начала"))
    expires_at = models.DateTimeField(_("Дата окончания"))
    is_active = models.BooleanField(_("Активна"), default=True)
    payment_id = models.CharField(_("ID платежа"), max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = _("Премиум-подписка")
        verbose_name_plural = _("Премиум-подписки")
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_plan_type_display()} (до {self.expires_at.strftime('%d.%m.%Y')})"
