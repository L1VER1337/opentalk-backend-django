from django.shortcuts import render, get_object_or_404
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
        ).distinct()