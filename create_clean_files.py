#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для создания новых файлов в приложении messages_api с правильной кодировкой.
"""

import os
import shutil

# Определяем пути
PROJECT_DIR = os.path.abspath('.')
MESSAGES_API_DIR = os.path.join(PROJECT_DIR, 'messages_api')
TEMP_DIR = os.path.join(PROJECT_DIR, 'messages_api_new')

# Содержимое файлов
VIEWS_CONTENT = '''from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Max, F, Value, BooleanField
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from .models import Chat, Message, Attachment
from .serializers import (
    ChatSerializer, MessageSerializer, AttachmentSerializer,
    ChatListSerializer, MessageCreateSerializer, MessageReadSerializer
)

User = get_user_model()


class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с чатами
    """
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Возвращает все чаты пользователя с дополнительной информацией:
        - количество непрочитанных сообщений
        - последнее сообщение
        """
        user = self.request.user
        
        # Находим все чаты, где участвует пользователь
        chats = Chat.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).annotate(
            # Количество непрочитанных сообщений
            unread_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
            ),
            # Последнее сообщение
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time')
        
        return chats
    
    def retrieve(self, request, *args, **kwargs):
        """
        Получение данных конкретного чата
        """
        chat = self.get_object()
        user = request.user
        
        # Проверяем, что пользователь является участником чата
        if chat.user1 != user and chat.user2 != user:
            return Response(
                {"detail": "У вас нет доступа к этому чату."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(chat)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        """
        Получение списка всех чатов пользователя
        """
        queryset = self.get_queryset()
        serializer = ChatListSerializer(
            queryset, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Создание нового чата с пользователем
        """
        user = request.user
        user_id = request.data.get('userId')
        
        if not user_id:
            return Response(
                {"detail": "Необходимо указать userId."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Пользователь не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем, существует ли уже чат между пользователями
        existing_chat = Chat.objects.filter(
            (Q(user1=user) & Q(user2=other_user)) |
            (Q(user1=other_user) & Q(user2=user))
        ).first()
        
        if existing_chat:
            serializer = self.get_serializer(existing_chat)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Создаем новый чат
        chat = Chat.objects.create(user1=user, user2=other_user)
        
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Получение сообщений конкретного чата
        """
        chat = self.get_object()
        user = request.user
        
        # Проверяем, что пользователь является участником чата
        if chat.user1 != user and chat.user2 != user:
            return Response(
                {"detail": "У вас нет доступа к этому чату."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Параметры пагинации и сортировки
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        sort_order = request.query_params.get('sortOrder', 'asc')
        
        # Получаем сообщения
        messages = chat.messages.all()
        
        # Сортировка
        if sort_order == 'asc':
            messages = messages.order_by('timestamp')
        else:
            messages = messages.order_by('-timestamp')
        
        # Пагинация
        messages = messages[offset:offset + limit]
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Отправка нового сообщения в чат
        """
        chat = self.get_object()
        user = request.user
        
        # Проверяем, что пользователь является участником чата
        if chat.user1 != user and chat.user2 != user:
            return Response(
                {"detail": "У вас нет доступа к этому чату."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Создание сериализатора с данными запроса
        serializer = MessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Сохраняем сообщение
            message = serializer.save(chat=chat, sender=user)
            
            # Обработка вложений, если есть
            attachments = request.data.get('attachments', [])
            if attachments:
                for attachment_id in attachments:
                    try:
                        attachment = Attachment.objects.get(id=attachment_id, uploader=user)
                        message.attachments.add(attachment)
                    except Attachment.DoesNotExist:
                        pass
            
            # Возвращаем данные созданного сообщения
            return Response(
                MessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'], url_path='messages/read')
    def mark_messages_as_read(self, request, pk=None):
        """
        Отметка сообщений как прочитанных
        """
        chat = self.get_object()
        user = request.user
        
        # Проверяем, что пользователь является участником чата
        if chat.user1 != user and chat.user2 != user:
            return Response(
                {"detail": "У вас нет доступа к этому чату."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageReadSerializer(data=request.data)
        if serializer.is_valid():
            message_ids = serializer.validated_data.get('message_ids', [])
            
            # Если список ID пуст, отмечаем все непрочитанные сообщения
            if not message_ids:
                updated_count = Message.objects.filter(
                    chat=chat,
                    is_read=False,
                    sender__ne=user
                ).update(is_read=True)
            else:
                # Отмечаем указанные сообщения как прочитанные
                updated_count = Message.objects.filter(
                    id__in=message_ids,
                    chat=chat,
                    is_read=False,
                    sender__ne=user
                ).update(is_read=True)
            
            return Response({
                "status": "success",
                "updated_count": updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с сообщениями (только для чтения)
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Получение сообщений, к которым у пользователя есть доступ
        """
        user = self.request.user
        
        # Получение всех сообщений из чатов, где пользователь участвует
        return Message.objects.filter(
            Q(chat__user1=user) | Q(chat__user2=user)
        ).select_related('chat', 'sender')
    
    @action(detail=False, methods=['get'], url_path='search')
    def search_messages(self, request):
        """
        Поиск по сообщениям
        """
        user = request.user
        query = request.query_params.get('q', '')
        chat_id = request.query_params.get('chatId')
        limit = int(request.query_params.get('limit', 20))
        
        if not query:
            return Response({"detail": "Поисковый запрос не может быть пустым."}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        messages = self.get_queryset().filter(content__icontains=query)
        
        # Если указан ID чата, ограничиваем поиск этим чатом
        if chat_id:
            messages = messages.filter(chat_id=chat_id)
        
        # Ограничение количества результатов
        messages = messages[:limit]
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с вложениями
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        При создании вложения, автоматически устанавливаем текущего пользователя
        """
        serializer.save(uploader=self.request.user)
    
    def get_queryset(self):
        """
        Пользователь может видеть только свои вложения или вложения из своих чатов
        """
        user = self.request.user
        
        return Attachment.objects.filter(
            Q(uploader=user) |
            Q(messages__chat__user1=user) |
            Q(messages__chat__user2=user)
        ).distinct()'''

MODELS_CONTENT = '''from django.db import models
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
        return f"Сообщение от {self.sender.username} в {self.chat}"'''

SERIALIZERS_CONTENT = '''from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.serializers import UserMiniSerializer
from .models import Chat, Message, Attachment

User = get_user_model()


class AttachmentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вложений
    """
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_url', 'file_type', 'file_name', 'file_size', 'upload_date', 'uploader']
        read_only_fields = ['upload_date', 'uploader']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class MessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сообщений
    """
    sender = UserMiniSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'content', 'timestamp', 'is_read', 'attachments']
        read_only_fields = ['chat', 'sender', 'timestamp', 'is_read']


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новых сообщений
    """
    class Meta:
        model = Message
        fields = ['content']


class MessageReadSerializer(serializers.Serializer):
    """
    Сериализатор для отметки сообщений как прочитанных
    """
    message_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False
    )


class LastMessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для последнего сообщения в чате (для списка чатов)
    """
    class Meta:
        model = Message
        fields = ['content', 'timestamp']


class ChatSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детальной информации о чате
    """
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = ['id', 'user', 'created_at', 'is_pinned']
    
    def get_user(self, obj):
        """
        Возвращает информацию о собеседнике (не о текущем пользователе)
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            current_user = request.user
            other_user = obj.user1 if obj.user2 == current_user else obj.user2
            return UserMiniSerializer(other_user).data
        return None


class ChatListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка чатов с дополнительной информацией
    """
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Chat
        fields = ['id', 'user', 'last_message', 'unread_count', 'is_pinned', 'created_at']
    
    def get_user(self, obj):
        """
        Возвращает информацию о собеседнике (не о текущем пользователе)
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            current_user = request.user
            other_user = obj.user1 if obj.user2 == current_user else obj.user2
            return UserMiniSerializer(other_user).data
        return None
    
    def get_last_message(self, obj):
        """
        Возвращает последнее сообщение в чате
        """
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return LastMessageSerializer(last_message).data
        return None'''

ADMIN_CONTENT = '''from django.contrib import admin
from .models import Chat, Message, Attachment


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    """
    Административная панель для чатов
    """
    list_display = ('id', 'user1', 'user2', 'created_at', 'is_pinned')
    list_filter = ('is_pinned', 'created_at')
    search_fields = ('user1__username', 'user2__username')
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Административная панель для сообщений
    """
    list_display = ('id', 'chat', 'sender', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('content', 'sender__username')
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        """
        Превью содержимого сообщения (максимум 50 символов)
        """
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    
    content_preview.short_description = "Содержимое"


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """
    Административная панель для вложений
    """
    list_display = ('id', 'file_name', 'file_type', 'file_size_display', 'uploader', 'upload_date')
    list_filter = ('file_type', 'upload_date')
    search_fields = ('file_name', 'uploader__username')
    date_hierarchy = 'upload_date'
    
    def file_size_display(self, obj):
        """
        Отображение размера файла в человекочитаемом формате
        """
        size = obj.file_size
        
        if size < 1024:
            return f"{size} байт"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} КБ"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} МБ"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} ГБ"
    
    file_size_display.short_description = "Размер файла"'''

APPS_CONTENT = '''from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MessagesApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messages_api'
    verbose_name = _('Чаты и сообщения')'''

INIT_CONTENT = ''''''

def create_or_clean_dir(dir_path):
    """Создает или очищает директорию"""
    if os.path.exists(dir_path):
        # Очищаем директорию
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        # Создаем директорию
        os.makedirs(dir_path)

def create_file(path, content):
    """Создает файл с указанным содержимым"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Создан файл: {path}")

def main():
    print("Создание новой структуры файлов для приложения messages_api...")
    
    # Создаем или очищаем временную директорию
    create_or_clean_dir(TEMP_DIR)
    
    # Создаем файлы
    create_file(os.path.join(TEMP_DIR, 'views.py'), VIEWS_CONTENT)
    create_file(os.path.join(TEMP_DIR, 'models.py'), MODELS_CONTENT)
    create_file(os.path.join(TEMP_DIR, 'serializers.py'), SERIALIZERS_CONTENT)
    create_file(os.path.join(TEMP_DIR, 'admin.py'), ADMIN_CONTENT)
    create_file(os.path.join(TEMP_DIR, 'apps.py'), APPS_CONTENT)
    create_file(os.path.join(TEMP_DIR, '__init__.py'), INIT_CONTENT)
    
    # Создаем директорию migrations, если ее нет
    migrations_dir = os.path.join(TEMP_DIR, 'migrations')
    os.makedirs(migrations_dir, exist_ok=True)
    create_file(os.path.join(migrations_dir, '__init__.py'), INIT_CONTENT)
    
    print("\nФайлы успешно созданы в директории messages_api_new.")
    print("Теперь вы можете заменить старую директорию messages_api на новую следующими командами:")
    print("\n1. Удалите старую директорию (выполните в PowerShell или CMD):")
    print(f"   rm -r {MESSAGES_API_DIR}")
    print("\n2. Переименуйте новую директорию:")
    print(f"   mv {TEMP_DIR} {MESSAGES_API_DIR}")
    print("\nПосле этого попробуйте выполнить миграции:")
    print("   py manage.py makemigrations")
    print("   py manage.py migrate")

if __name__ == "__main__":
    main() 