from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class VoiceChannel(models.Model):
    """
    Модель голосового канала
    """
    name = models.CharField(_("Название"), max_length=255)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_voice_channels', 
                              verbose_name=_("Создатель"))
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    max_participants = models.PositiveIntegerField(_("Максимум участников"), default=10)
    
    class Meta:
        verbose_name = _("Голосовой канал")
        verbose_name_plural = _("Голосовые каналы")
    
    def __str__(self):
        return f"Канал: {self.name} ({self.creator.username})"


class VoiceChannelMember(models.Model):
    """
    Модель участника голосового канала
    """
    channel = models.ForeignKey(VoiceChannel, on_delete=models.CASCADE, related_name='members', 
                              verbose_name=_("Канал"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_channels', 
                           verbose_name=_("Пользователь"))
    joined_at = models.DateTimeField(_("Время присоединения"), auto_now_add=True)
    mic_status = models.BooleanField(_("Микрофон включен"), default=True)
    speaker_status = models.BooleanField(_("Динамик включен"), default=True)
    
    class Meta:
        verbose_name = _("Участник голосового канала")
        verbose_name_plural = _("Участники голосовых каналов")
        unique_together = ('channel', 'user')  # Пользователь может быть в канале только один раз
    
    def __str__(self):
        return f"{self.user.username} в канале {self.channel.name}"


class Call(models.Model):
    """
    Модель звонка между пользователями
    """
    STATUS_CHOICES = (
        ('missed', 'Пропущенный'),
        ('answered', 'Отвеченный'),
        ('declined', 'Отклоненный'),
    )
    
    TYPE_CHOICES = (
        ('audio', 'Аудио'),
        ('video', 'Видео'),
    )
    
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls', 
                             verbose_name=_("Звонящий"))
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls', 
                               verbose_name=_("Получатель"))
    started_at = models.DateTimeField(_("Время начала"), auto_now_add=True)
    ended_at = models.DateTimeField(_("Время окончания"), null=True, blank=True)
    status = models.CharField(_("Статус"), max_length=10, choices=STATUS_CHOICES, default='missed')
    call_type = models.CharField(_("Тип звонка"), max_length=10, choices=TYPE_CHOICES, default='audio')
    
    class Meta:
        verbose_name = _("Звонок")
        verbose_name_plural = _("Звонки")
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.caller.username} -> {self.receiver.username} ({self.get_status_display()})"
    
    @property
    def duration(self):
        """Длительность звонка в секундах"""
        if self.status == 'answered' and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0
