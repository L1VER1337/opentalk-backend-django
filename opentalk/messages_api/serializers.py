from rest_framework import serializers
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
        return None