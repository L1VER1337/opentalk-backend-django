from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from .models import Notification, PremiumSubscription
from .serializers import NotificationSerializer, PremiumSubscriptionSerializer, PremiumPlanSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с уведомлениями пользователя
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает уведомления текущего пользователя"""
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def read_all(self, request):
        """Отметить все уведомления как прочитанные"""
        notifications = self.get_queryset().filter(is_read=False)
        notifications.update(is_read=True)
        return Response({"status": "Все уведомления отмечены как прочитанные"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def read(self, request, pk=None):
        """Отметить уведомление как прочитанное"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "Уведомление отмечено как прочитанное"}, status=status.HTTP_200_OK)


class PremiumViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с премиум-подписками пользователя
    """
    serializer_class = PremiumSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает премиум-подписки текущего пользователя"""
        return PremiumSubscription.objects.filter(user=self.request.user).order_by('-started_at')
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def status(self, request):
        """Проверка статуса премиум-подписки пользователя"""
        user = request.user
        
        # Проверяем, есть ли активная подписка
        active_subscription = PremiumSubscription.objects.filter(
            user=user, 
            is_active=True, 
            expires_at__gt=datetime.now()
        ).first()
        
        if not active_subscription:
            return Response({
                "is_premium": False,
                "message": "У вас нет активной премиум-подписки."
            })
        
        # Форматируем ответ с информацией о подписке
        return Response({
            "is_premium": True,
            "plan_type": active_subscription.get_plan_type_display(),
            "expires_at": active_subscription.expires_at,
            "days_left": (active_subscription.expires_at - datetime.now()).days
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def plans(self, request):
        """Получение списка доступных премиум-планов"""
        plans = [
            {
                "type": "monthly",
                "name": "Месячная подписка",
                "price": 299.00,
                "duration_days": 30,
                "features": [
                    "Отсутствие рекламы",
                    "Расширенная статистика",
                    "Приоритетная поддержка",
                    "Расширенные настройки приватности"
                ]
            },
            {
                "type": "yearly",
                "name": "Годовая подписка",
                "price": 2990.00,
                "duration_days": 365,
                "features": [
                    "Отсутствие рекламы",
                    "Расширенная статистика",
                    "Приоритетная поддержка",
                    "Расширенные настройки приватности",
                    "Эксклюзивные стикеры",
                    "Расширенные функции сообщений"
                ]
            }
        ]
        
        serializer = PremiumPlanSerializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request):
        """Оформление новой премиум-подписки"""
        user = request.user
        plan_type = request.data.get('plan_type')
        payment_id = request.data.get('payment_id')
        
        # Проверка корректности плана
        if plan_type not in ['monthly', 'yearly']:
            return Response(
                {"error": "Некорректный тип плана. Доступные типы: monthly, yearly"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Определение дат начала и окончания подписки
        started_at = datetime.now()
        if plan_type == 'monthly':
            expires_at = started_at + timedelta(days=30)
        else:  # yearly
            expires_at = started_at + timedelta(days=365)
        
        # Создание новой подписки
        subscription = PremiumSubscription.objects.create(
            user=user,
            plan_type=plan_type,
            started_at=started_at,
            expires_at=expires_at,
            is_active=True,
            payment_id=payment_id
        )
        
        # Обновление флага премиум-пользователя
        user.is_premium = True
        user.save()
        
        serializer = PremiumSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request):
        """Отмена премиум-подписки"""
        user = request.user
        
        # Находим активную подписку
        subscription = PremiumSubscription.objects.filter(
            user=user, 
            is_active=True
        ).first()
        
        if not subscription:
            return Response(
                {"error": "У вас нет активной подписки для отмены."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Отключаем подписку
        subscription.is_active = False
        subscription.save()
        
        # Если срок подписки истек, убираем флаг премиум
        if subscription.expires_at <= datetime.now():
            user.is_premium = False
            user.save()
        
        return Response({"status": "Подписка успешно отменена"}, status=status.HTTP_200_OK)
