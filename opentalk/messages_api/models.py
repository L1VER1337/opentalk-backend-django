from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Chat(models.Model):
    """
    Модель чата между двумя пользователями
    """
    user1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chats_as_user1',
        verbose_name=_("Первый пользователь")
    )
    user2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chats_as_user2',
        verbose_name=_("Второй пользователь")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name=_("Закреплен")
    )
    
    class Meta:
        verbose_name = _("Чат")
        verbose_name_plural = _("Чаты")
        # Уникальное ограничение для пары пользователей
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"Чат между {self.user1.username} и {self.user2.username}"


class Attachment(models.Model):
    """
    Модель для вложений в сообщениях
    """
    file = models.FileField(
        upload_to='chat_attachments/',
        verbose_name=_("Файл")
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Тип файла")
    )
    file_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Имя файла")
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Размер файла (байт)")
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата загрузки")
    )
    uploader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments',
        verbose_name=_("Кто загрузил")
    )
    
    class Meta:
        verbose_name = _("Вложение")
        verbose_name_plural = _("Вложения")
    
    def __str__(self):
        return f"Вложение {self.file_name} от {self.uploader.username}"
    
    def save(self, *args, **kwargs):
        # Если файл только что загружен, автоматически заполняем метаданные
        if self.file and not self.file_name:
            self.file_name = self.file.name.split('/')[-1]
            self.file_size = self.file.size
            # Определение типа файла по расширению
            extension = self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''
            if extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                self.file_type = 'image'
            elif extension in ['mp4', 'avi', 'mov', 'webm']:
                self.file_type = 'video'
            elif extension in ['mp3', 'wav', 'ogg']:
                self.file_type = 'audio'
            elif extension in ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx']:
                self.file_type = 'document'
            else:
                self.file_type = 'other'
        
        super().save(*args, **kwargs)


class Message(models.Model):
    """
    Модель сообщения в чате
    """
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Чат")
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_("Отправитель")
    )
    content = models.TextField(
        verbose_name=_("Содержание")
    )
    attachments = models.ManyToManyField(
        Attachment,
        related_name='messages',
        blank=True,
        verbose_name=_("Вложения")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата отправки")
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Прочитано")
    )
    
    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Сообщение от {self.sender.username} в {self.chat}"