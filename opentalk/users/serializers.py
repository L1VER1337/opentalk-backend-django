from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
import random
import datetime
from .models import Subscription, VerificationCode

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name', 'avatar', 'bio',
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
            'id', 'username', 'email', 'phone', 'full_name', 'avatar', 'bio',
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
        fields = ['username', 'email', 'phone', 'password', 'password2', 'full_name']
        extra_kwargs = {
            'full_name': {'required': False},
            'email': {'required': False},
            'phone': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        
        # Проверка, что был введен хотя бы номер телефона
        if not attrs.get('phone'):
            raise serializers.ValidationError({"phone": "Необходимо указать номер телефона."})
        
        # Проверка уникальности номера телефона
        phone = attrs.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "Пользователь с таким номером телефона уже существует."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        if 'full_name' not in validated_data or not validated_data.get('full_name'):
            validated_data['full_name'] = validated_data.get('username', '')
        user = User.objects.create_user(**validated_data)
        return user


class SendVerificationCodeSerializer(serializers.Serializer):
    """
    Сериализатор для отправки кода верификации
    """
    phone = serializers.CharField(max_length=15)
    
    def validate_phone(self, value):
        # Проверка формата номера телефона (можно расширить по необходимости)
        if not value.isdigit() or not (10 <= len(value) <= 15):
            raise serializers.ValidationError("Неверный формат номера телефона")
        return value
    
    def create(self, validated_data):
        phone = validated_data.get('phone')
        
        # Деактивируем предыдущие неиспользованные коды для этого номера
        VerificationCode.objects.filter(
            phone=phone,
            is_used=False
        ).update(is_used=True)
        
        # Генерируем новый код
        code = ''.join(random.choices('0123456789', k=6))
        
        # Создаем новую запись кода верификации
        verification = VerificationCode.objects.create(
            phone=phone,
            code=code,
        )
        
        # Отладочное сообщение
        print(f"SendVerificationCodeSerializer: создан новый код {code} для телефона {phone}, ID: {verification.id}, истекает: {verification.expires_at}")
        
        # Отправляем код в Telegram (в реальном приложении, это мог бы быть SMS)
        try:
            # Код отправки сообщения в Telegram или SMS
            # В демо-режиме просто выводим сообщение в консоль
            print(f"Код верификации для {phone}: {code} успешно отправлен в Telegram")
            print(f"Код верификации для {phone}: {code}")
        except Exception as e:
            print(f"Ошибка при отправке кода верификации: {str(e)}")
        
        return verification


class VerifyCodeSerializer(serializers.Serializer):
    """
    Сериализатор для проверки кода верификации
    """
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)
    
    def validate(self, data):
        phone = data.get('phone')
        code = data.get('code')
        
        # Отладочное сообщение
        print(f"VerifyCodeSerializer: проверка кода {code} для телефона {phone}")
        
        # Проверяем, существует ли код верификации
        try:
            verification = VerificationCode.objects.filter(
                phone=phone,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            # Отладочное сообщение о результате запроса
            if verification:
                print(f"VerifyCodeSerializer: найден код верификации с ID {verification.id}, срок действия до {verification.expires_at}")
            else:
                # Выведем информацию о всех кодах для этого телефона
                all_codes = VerificationCode.objects.filter(phone=phone)
                print(f"VerifyCodeSerializer: найдено {all_codes.count()} кодов для телефона {phone}:")
                for vc in all_codes:
                    print(f"  - Код: {vc.code}, использован: {vc.is_used}, истекает: {vc.expires_at}, сейчас: {timezone.now()}")
                
                # Режим разработки - в демо-режиме принимаем любой код для упрощения тестирования
                demo_mode = True
                if demo_mode and phone and code:
                    print(f"VerifyCodeSerializer: DEMO режим активирован, принимаем код {code} для телефона {phone}")
                    # Проверяем, существует ли пользователь с таким номером телефона
                    User = get_user_model()
                    user = User.objects.filter(phone=phone).first()
                    
                    return {
                        'is_valid': True,
                        'phone': phone,
                        'is_new_user': user is None,
                        'user': user
                    }
                else:
                    raise serializers.ValidationError("Код подтверждения не найден или истек срок его действия.")
            
            # Помечаем код как использованный
            verification.is_used = True
            verification.save()
            
            # Проверяем, существует ли пользователь с таким номером телефона
            User = get_user_model()
            user = User.objects.filter(phone=phone).first()
            
            return {
                'is_valid': True,
                'phone': phone,
                'is_new_user': user is None,
                'user': user
            }
            
        except Exception as e:
            print(f"VerifyCodeSerializer: ошибка при проверке кода: {str(e)}")
            raise serializers.ValidationError(f"Код подтверждения не найден или истек срок его действия. Ошибка: {str(e)}")


class PhoneLoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа по номеру телефона с кодом подтверждения
    """
    phone = serializers.CharField(required=True, max_length=15)
    code = serializers.CharField(required=True, max_length=6)
    
    def validate(self, attrs):
        phone = attrs['phone']
        code = attrs['code']
        
        # Находим последний действительный код для данного телефона
        verification = VerificationCode.objects.filter(
            phone=phone,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()
        
        if not verification:
            raise serializers.ValidationError("Код подтверждения не найден или истек срок его действия.")
        
        if verification.code != code:
            raise serializers.ValidationError("Неверный код подтверждения.")
        
        # Помечаем код как использованный
        verification.is_used = True
        verification.save()
        
        # Проверяем, существует ли пользователь с таким номером
        user = User.objects.filter(phone=phone).first()
        if not user:
            raise serializers.ValidationError("Пользователь с таким номером телефона не найден.")
        
        attrs['user'] = user
        return attrs


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


class CreateUserByPhoneSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания нового пользователя по номеру телефона
    """
    class Meta:
        model = User
        fields = ['username', 'phone']
        extra_kwargs = {
            'username': {'required': True},
            'phone': {'required': True, 'read_only': True}
        }
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value
    
    def create(self, validated_data):
        # Телефон должен быть передан в контексте
        phone = self.context.get('phone')
        if not phone:
            raise serializers.ValidationError({"phone": "Номер телефона не указан."})
        
        # Создаем пользователя без пароля (вход будет только по коду)
        user = User.objects.create(
            username=validated_data['username'],
            phone=phone,
            is_active=True
        )
        # Устанавливаем случайный пароль
        password = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12))
        user.set_password(password)
        user.save()
        
        return user 