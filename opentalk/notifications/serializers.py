from rest_framework import serializers
from .models import Notification, PremiumSubscription
from users.serializers import UserMiniSerializer


class NotificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уведомлений
    """
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'type', 'content', 'reference_id', 
            'reference_type', 'created_at', 'is_read'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class PremiumSubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для премиум-подписок
    """
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = PremiumSubscription
        fields = [
            'id', 'user', 'plan_type', 'started_at', 
            'expires_at', 'is_active', 'payment_id'
        ]
        read_only_fields = ['id', 'user', 'started_at']


class PremiumPlanSerializer(serializers.Serializer):
    """
    Сериализатор для планов премиум-подписки
    """
    type = serializers.CharField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration_days = serializers.IntegerField()
    features = serializers.ListField(child=serializers.CharField())
    
    class Meta:
        fields = ['type', 'name', 'price', 'duration_days', 'features']
