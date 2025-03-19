from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Subscription
from .serializers import (
    UserSerializer, UserProfileSerializer, UserMiniSerializer,
    RegisterSerializer, SubscriptionSerializer, ChangePasswordSerializer
)
from posts.serializers import PostSerializer

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
