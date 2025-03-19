from rest_framework import serializers
from .models import Chat, Message, ChatMember
from users.serializers import UserMiniSerializer


class MessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сообщений в чате
    """
    sender = UserMiniSerializer(read_only=True)
    media = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'content', 'media', 
            'created_at', 'is_read', 'is_edited'
        ]
        read_only_fields = ['id', 'sender', 'created_at']
    
    def get_media(self, obj):
        """Возвращает медиа-вложения сообщения"""
        return obj.get_media_urls()


class ChatMemberSerializer(serializers.ModelSerializer):
    """
    Сериализатор для участников чата
    """
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = ChatMember
        fields = ['id', 'chat', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class ChatSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чатов
    """
    members = ChatMemberSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Chat
        fields = [
            'id', 'name', 'is_group', 'created_at', 'updated_at', 
            'avatar', 'members', 'last_message', 'unread_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Возвращает последнее сообщение в чате"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'sender': UserMiniSerializer(last_message.sender).data,
                'content': last_message.content[:100],  # Только первые 100 символов
                'created_at': last_message.created_at,
                'is_read': last_message.is_read
            }
        return None
    
    def get_unread_count(self, obj):
        """Возвращает количество непрочитанных сообщений для текущего пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            # Получаем объект участника чата для текущего пользователя
            chat_member = ChatMember.objects.filter(chat=obj, user=user).first()
            if chat_member and chat_member.last_read_message:
                # Считаем сообщения после последнего прочитанного
                return obj.messages.filter(
                    created_at__gt=chat_member.last_read_message.created_at
                ).count()
            else:
                # Если нет последнего прочитанного, считаем все сообщения
                return obj.messages.count()
        return 0


class CreateMessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания нового сообщения
    """
    media = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Message
        fields = ['chat', 'content', 'media']
    
    def create(self, validated_data):
        media = validated_data.pop('media', []) if 'media' in validated_data else []
        
        message = Message.objects.create(
            sender=self.context['request'].user,
            **validated_data
        )
        
        if media:
            message.set_media_urls(media)
            message.save()
        
        # Обновляем время последнего обновления чата
        chat = validated_data.get('chat')
        chat.updated_at = message.created_at
        chat.save()
        
        return message 