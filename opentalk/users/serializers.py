from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'avatar', 'bio',
            'status', 'location', 'created_at', 'last_login', 
            'is_premium', 'is_verified', 'theme_preference'
        ]
        read_only_fields = ['id', 'created_at', 'last_login', 'is_premium', 'is_verified']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Расширенный сериализатор для профиля пользователя
    """
    followers_count = serializers.SerializerMethodField(read_only=True)
    following_count = serializers.SerializerMethodField(read_only=True)
    posts_count = serializers.SerializerMethodField(read_only=True)
    is_following = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'avatar', 'bio',
            'status', 'location', 'created_at', 'last_login', 
            'is_premium', 'is_verified', 'theme_preference',
            'followers_count', 'following_count', 'posts_count', 'is_following'
        ]
        read_only_fields = ['id', 'created_at', 'last_login', 'is_premium', 'is_verified']
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_posts_count(self, obj):
        return obj.posts.count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(follower=request.user, followed=obj).exists()
        return False


class UserMiniSerializer(serializers.ModelSerializer):
    """
    Упрощенный сериализатор пользователя для вложенных представлений
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar', 'is_verified']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'full_name']
        extra_kwargs = {
            'full_name': {'required': False},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        if 'full_name' not in validated_data or not validated_data.get('full_name'):
            validated_data['full_name'] = validated_data.get('username', '')
        user = User.objects.create_user(**validated_data)
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок между пользователями
    """
    follower = UserMiniSerializer(read_only=True)
    followed = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'follower', 'followed', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Сериализатор для изменения пароля
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Новые пароли не совпадают."})
        return attrs 


class UserStatusSerializer(serializers.Serializer):
    """
    Сериализатор для обновления статуса пользователя
    """
    status = serializers.ChoiceField(choices=User.STATUS_CHOICES)
    
    def validate_status(self, value):
        if value == 'do_not_disturb':
            return 'dnd'
        return value
    
    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance 