from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
import json


class Chat(models.Model):
    """
    Модель чата (личные и групповые чаты)
    """
    name = models.CharField(_("Название"), max_length=255, blank=True, null=True)
    is_group = models.BooleanField(_("Групповой чат"), default=False)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)
    avatar = models.ImageField(_("Аватар"), upload_to='chat_avatars/', null=True, blank=True)
    
    class Meta:
        verbose_name = _("Чат")
        verbose_name_plural = _("Чаты")
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group and self.name:
            return f"Групповой чат: {self.name}"
        return f"Чат {self.id}"


class ChatMember(models.Model):
    """
    Модель участника чата
    """
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('member', 'Участник'),
    )
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='members', verbose_name=_("Чат"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats', verbose_name=_("Пользователь"))
    role = models.CharField(_("Роль"), max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(_("Дата присоединения"), auto_now_add=True)
    last_read_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='+', verbose_name=_("Последнее прочитанное сообщение"))
    
    class Meta:
        verbose_name = _("Участник чата")
        verbose_name_plural = _("Участники чатов")
        unique_together = ('chat', 'user')  # Пользователь может быть в чате только один раз
    
    def __str__(self):
        return f"{self.user.username} в чате {self.chat.id} ({self.role})"


class Message(models.Model):
    """
    Модель сообщения в чате
    """
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', verbose_name=_("Чат"))
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name=_("Отправитель"))
    content = models.TextField(_("Содержание"))
    media_urls = models.TextField(_("Медиа"), blank=True, null=True)
    created_at = models.DateTimeField(_("Дата отправки"), auto_now_add=True)
    is_read = models.BooleanField(_("Прочитано"), default=False)
    is_edited = models.BooleanField(_("Отредактировано"), default=False)
    
    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} в чате {self.chat.id}: {self.content[:30]}"
    
    def get_media_urls(self):
        if self.media_urls:
            return json.loads(self.media_urls)
        return []
    
    def set_media_urls(self, urls_list):
        self.media_urls = json.dumps(urls_list)
