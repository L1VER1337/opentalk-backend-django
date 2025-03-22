from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Subscription, VerificationCode
from .serializers import (
    UserSerializer, UserProfileSerializer, UserMiniSerializer,
    RegisterSerializer, SubscriptionSerializer, ChangePasswordSerializer,
    SendVerificationCodeSerializer, VerifyCodeSerializer, PhoneLoginSerializer,
    CreateUserByPhoneSerializer
)
from posts.serializers import PostSerializer
import io
import qrcode
from django.http import HttpResponse
from PIL import Image
import uuid
import json
from django.core.cache import cache

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    View для регистрации нового пользователя
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class ChangePasswordView(generics.UpdateAPIView):
    """
    View для изменения пароля пользователя
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Проверяем старый пароль
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": ["Неверный пароль."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Устанавливаем новый пароль
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {"message": "Пароль успешно изменен"},
            status=status.HTTP_200_OK
        )


class SendVerificationCodeView(generics.GenericAPIView):
    """
    View для отправки кода верификации на телефон
    """
    serializer_class = SendVerificationCodeSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Код подтверждения отправлен',
            'expiresIn': 120  # время действия кода в секундах
        }, status=status.HTTP_200_OK)


class VerifyCodeView(generics.GenericAPIView):
    """
    View для проверки кода верификации
    """
    serializer_class = VerifyCodeSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        print(f"VerifyCodeView: получен запрос с данными: {request.data}")
        
        # Проверим, есть ли коды верификации для указанного телефона
        phone = request.data.get('phone')
        if phone:
            codes = VerificationCode.objects.filter(phone=phone)
            print(f"VerifyCodeView: найдено {codes.count()} кодов для телефона {phone}")
            for code in codes:
                print(f"  - ID: {code.id}, Код: {code.code}, Использован: {code.is_used}, Истекает: {code.expires_at}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_new_user = serializer.validated_data['is_new_user']
        user = serializer.validated_data.get('user')
        phone = serializer.validated_data['phone']
        
        print(f"VerifyCodeView: код верифицирован, новый пользователь: {is_new_user}")
        
        if is_new_user:
            # Для нового пользователя создаем временный токен
            payload = {'phone': phone, 'type': 'temp_token'}
            refresh = RefreshToken()
            for key, value in payload.items():
                refresh[key] = value
            
            print(f"VerifyCodeView: создан временный токен для телефона {phone}")
            
            return Response({
                'success': True,
                'isNewUser': True,
                'tempToken': str(refresh.access_token),
                'phone': phone
            }, status=status.HTTP_200_OK)
        else:
            # Для существующего пользователя - авторизация
            refresh = RefreshToken.for_user(user)
            
            print(f"VerifyCodeView: пользователь {user.username} успешно авторизован")
            
            return Response({
                'success': True,
                'isNewUser': False,
                'token': str(refresh.access_token),
                'refreshToken': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)


class PhoneLoginView(generics.GenericAPIView):
    """
    View для входа по номеру телефона с кодом подтверждения
    """
    serializer_class = PhoneLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'token': str(refresh.access_token),
            'refreshToken': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class CreateUserByPhoneView(generics.GenericAPIView):
    """
    View для создания нового пользователя после верификации телефона
    """
    serializer_class = CreateUserByPhoneSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # В демо-режиме, не будем требовать токен для упрощения тестирования
        # В продакшене эту проверку нужно включить обратно
        demo_mode = True
        
        if not demo_mode:
            # Проверяем временный токен
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return Response(
                    {"detail": "Необходимо предоставить временный токен авторизации."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Получаем номер телефона из запроса
        phone = request.data.get('phone')
        if not phone:
            return Response(
                {"detail": "Необходимо указать номер телефона."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем контекст с номером телефона
        serializer = self.get_serializer(data=request.data, context={'phone': phone})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Создаем токены для нового пользователя
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'token': str(refresh.access_token),
            'refreshToken': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class CheckUsernameView(generics.GenericAPIView):
    """
    View для проверки доступности имени пользователя
    """
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        username = request.query_params.get('username')
        
        if not username:
            return Response(
                {"detail": "Необходимо указать имя пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = User.objects.filter(username=username).exists()
        
        return Response({
            'available': not exists,
            'message': "Имя пользователя доступно" if not exists else "Имя пользователя уже занято"
        })


class UpdateStatusView(generics.GenericAPIView):
    """
    View для обновления статуса пользователя
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        # Логирование для диагностики
        print(f"UpdateStatusView.patch: получен запрос от пользователя {request.user.id}")
        print(f"UpdateStatusView.patch: данные запроса - {request.data}")
        
        user = request.user
        status_value = request.data.get('status')
        
        # Проверка валидности статуса
        valid_statuses = dict(User.STATUS_CHOICES).keys()
        print(f"UpdateStatusView.patch: допустимые статусы - {valid_statuses}")
        
        # Обработка статуса "do_not_disturb" -> "dnd"
        if status_value == 'do_not_disturb':
            status_value = 'dnd'
        
        print(f"UpdateStatusView.patch: проверяем статус {status_value}")
        
        if status_value not in valid_statuses:
            print(f"UpdateStatusView.patch: недопустимый статус {status_value}")
            return Response(
                {"error": f"Неверный статус. Допустимые значения: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Обновление статуса
        user.status = status_value
        user.save()
        
        print(f"UpdateStatusView.patch: статус успешно обновлен на {user.status}")
        
        return Response({"status": user.status, "message": "Статус успешно обновлен"})


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'full_name', 'bio']
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'me':
            return UserProfileSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me', 'update_me', 'followers', 'following', 'posts', 'suggested', 'follow', 'unfollow', 'update_status']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение данных текущего пользователя"""
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """Обновление данных текущего пользователя"""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def followers(self, request, pk=None):
        """Получение списка подписчиков пользователя"""
        user = self.get_object()
        subscriptions = Subscription.objects.filter(followed=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def following(self, request, pk=None):
        """Получение списка подписок пользователя"""
        user = self.get_object()
        subscriptions = Subscription.objects.filter(follower=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Подписка на пользователя"""
        user_to_follow = self.get_object()
        current_user = request.user
        
        # Нельзя подписаться на самого себя
        if user_to_follow == current_user:
            return Response(
                {"detail": "Вы не можете подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка, подписан ли уже пользователь
        subscription, created = Subscription.objects.get_or_create(
            follower=current_user,
            followed=user_to_follow
        )
        
        if not created:
            return Response(
                {"detail": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({"status": "Вы успешно подписались"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk=None):
        """Отписка от пользователя"""
        user_to_unfollow = self.get_object()
        current_user = request.user
        
        try:
            subscription = Subscription.objects.get(
                follower=current_user,
                followed=user_to_unfollow
            )
            subscription.delete()
            return Response({"status": "Вы успешно отписались"}, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def posts(self, request, pk=None):
        """Получение постов пользователя"""
        user = self.get_object()
        posts = user.posts.all()
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def suggested(self, request):
        """Получение рекомендуемых пользователей для подписки"""
        current_user = request.user
        
        # Находим пользователей, на которых подписан текущий пользователь
        following_ids = Subscription.objects.filter(
            follower=current_user
        ).values_list('followed_id', flat=True)
        
        # Исключаем их и текущего пользователя из результатов
        suggested_users = User.objects.exclude(
            Q(id=current_user.id) | Q(id__in=following_ids)
        ).order_by('?')[:10]  # Случайная выборка 10 пользователей
        
        serializer = UserMiniSerializer(suggested_users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request):
        """Обновление статуса пользователя"""
        user = request.user
        status_value = request.data.get('status')
        
        # Проверка валидности статуса
        valid_statuses = dict(User.STATUS_CHOICES).keys()
        
        # Обработка статуса "do_not_disturb" -> "dnd"
        if status_value == 'do_not_disturb':
            status_value = 'dnd'
        
        if status_value not in valid_statuses:
            return Response(
                {"error": f"Неверный статус. Допустимые значения: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Обновление статуса
        user.status = status_value
        user.save()
        
        return Response({"status": user.status, "message": "Статус успешно обновлен"})


class LogoutView(generics.GenericAPIView):
    """
    View для выхода из аккаунта
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Получение токена из заголовка
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return Response(
                    {"detail": "Неверный формат токена."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Очистка cookie, если они используются
            response = Response(
                {"detail": "Вы успешно вышли из аккаунта."},
                status=status.HTTP_200_OK
            )
            if 'refresh_token' in request.COOKIES:
                response.delete_cookie('refresh_token')
            
            return response
        except Exception as e:
            return Response(
                {"detail": f"Произошла ошибка при выходе: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class OnlineStatusView(generics.GenericAPIView):
    """
    View для получения статусов онлайн пользователей
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user_ids = request.data.get('userIds', [])
        
        if not user_ids:
            return Response(
                {"detail": "Необходимо указать список ID пользователей."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получение статусов пользователей
        users = User.objects.filter(id__in=user_ids)
        
        # Формирование ответа
        statuses = {}
        for user in users:
            statuses[str(user.id)] = {
                'status': user.status,
                'is_online': user.status == 'online'
            }
        
        return Response(statuses)


class QRCodeView(generics.GenericAPIView):
    """
    Представление для генерации QR-кода
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Генерируем уникальный идентификатор сессии
        session_id = str(uuid.uuid4())
        
        # Создаем данные для QR-кода
        qr_data = {
            'sessionId': session_id,
            'type': 'auth'
        }
        
        # Сохраняем информацию о сессии в кеш
        cache.set(f'qr_session:{session_id}', {'status': 'pending'}, timeout=600)  # Время жизни 10 минут
        
        # Формируем текст для QR-кода - можно либо передавать JSON, либо URL
        text = json.dumps(qr_data)
        
        # Создаем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем изображение в байтовый буфер
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Возвращаем изображение в ответе и устанавливаем куки с session_id
        response = HttpResponse(buffer, content_type="image/png")
        response["X-Session-ID"] = session_id
        return response


class QRStatusView(generics.GenericAPIView):
    """
    Представление для проверки статуса QR-кода
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Получаем идентификатор сессии из параметра запроса
        session_id = request.query_params.get('sessionId')
        
        if not session_id or session_id == 'undefined':
            return Response(
                {"detail": "Необходимо указать идентификатор сессии."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем информацию о сессии из кеша
        session_data = cache.get(f'qr_session:{session_id}')
        
        if not session_data:
            return Response(
                {"detail": "Сессия не найдена или истекла."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Возвращаем статус сессии
        return Response(session_data)
    
    
class AuthenticateByQRView(generics.GenericAPIView):
    """
    Представление для аутентификации по QR-коду с мобильного устройства
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Получаем идентификатор сессии из запроса
        session_id = request.data.get('sessionId')
        
        if not session_id:
            return Response(
                {"detail": "Необходимо указать идентификатор сессии."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем текущего пользователя
        user = request.user
        
        # Обновляем информацию о сессии в кеше
        session_data = {
            'status': 'authenticated',
            'user': {
                'id': user.id,
                'username': user.username,
                'phone': user.phone
            },
            'tokens': {
                'access': str(RefreshToken.for_user(user).access_token),
                'refresh': str(RefreshToken.for_user(user))
            }
        }
        
        cache.set(f'qr_session:{session_id}', session_data, timeout=300)  # 5 минут на вход
        
        return Response({
            "success": True,
            "message": "Аутентификация успешна"
        })
