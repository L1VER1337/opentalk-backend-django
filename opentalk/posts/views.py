from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Post, Comment, Like, Hashtag, Trend
from .serializers import (
    PostSerializer, CommentSerializer, CreateCommentSerializer,
    LikeSerializer, HashtagSerializer, TrendSerializer
)


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с постами
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['content']
    
    def get_queryset(self):
        """
        Фильтрация результатов на основе параметров запроса
        """
        queryset = Post.objects.all()
        
        # Получение параметров фильтрации из запроса
        username = self.request.query_params.get('username', None)
        hashtag = self.request.query_params.get('hashtag', None)
        
        if username is not None:
            queryset = queryset.filter(user__username=username)
        
        if hashtag is not None:
            queryset = queryset.filter(hashtags__hashtag__name=hashtag)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        """Получение комментариев поста"""
        post = self.get_object()
        comments = Comment.objects.filter(post=post, parent=None)  # Только родительские комментарии
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Поставить лайк на пост"""
        post = self.get_object()
        user = request.user
        
        like, created = Like.objects.get_or_create(
            user=user,
            content_type='post',
            content_id=post.id
        )
        
        if created:
            post.likes_count += 1
            post.save()
            return Response({"status": "Лайк добавлен"}, status=status.HTTP_201_CREATED)
        
        return Response({"status": "Пост уже лайкнут"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Убрать лайк с поста"""
        post = self.get_object()
        user = request.user
        
        try:
            like = Like.objects.get(
                user=user,
                content_type='post',
                content_id=post.id
            )
            like.delete()
            
            # Уменьшаем счетчик лайков
            if post.likes_count > 0:
                post.likes_count -= 1
                post.save()
            
            return Response({"status": "Лайк удален"}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response(
                {"detail": "Лайк не найден."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def repost(self, request, pk=None):
        """Сделать репост"""
        original_post = self.get_object()
        user = request.user
        
        # Проверка, не репостит ли пользователь свой пост
        if original_post.user == user:
            return Response({"error": "Нельзя репостить свои посты"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем репост
        repost = Post.objects.create(
            user=user,
            content=request.data.get('content', ''),
            is_repost=True,
            original_post=original_post
        )
        
        # Увеличиваем счетчик репостов у оригинального поста
        original_post.reposts_count += 1
        original_post.save()
        
        serializer = PostSerializer(repost, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def feed(self, request):
        """Получение ленты постов"""
        user = request.user
        
        # Получаем ID пользователей, на которых подписан текущий пользователь
        following_ids = user.following.values_list('followed_id', flat=True)
        
        # Получаем посты пользователей, на которых подписан текущий пользователь, и его собственные посты
        posts = Post.objects.filter(
            Q(user_id__in=following_ids) | Q(user=user)
        ).order_by('-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с комментариями
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCommentSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def replies(self, request, pk=None):
        """Получение ответов на комментарий"""
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment)
        page = self.paginate_queryset(replies)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Поставить лайк на комментарий"""
        comment = self.get_object()
        user = request.user
        
        like, created = Like.objects.get_or_create(
            user=user,
            content_type='comment',
            content_id=comment.id
        )
        
        if created:
            comment.likes_count += 1
            comment.save()
            return Response({"status": "Лайк добавлен"}, status=status.HTTP_201_CREATED)
        
        return Response({"status": "Комментарий уже лайкнут"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Убрать лайк с комментария"""
        comment = self.get_object()
        user = request.user
        
        try:
            like = Like.objects.get(
                user=user,
                content_type='comment',
                content_id=comment.id
            )
            like.delete()
            
            # Уменьшаем счетчик лайков
            if comment.likes_count > 0:
                comment.likes_count -= 1
                comment.save()
            
            return Response({"status": "Лайк удален"}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response(
                {"detail": "Лайк не найден."},
                status=status.HTTP_400_BAD_REQUEST
            )


class HashtagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с хештегами (только чтение)
    """
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def posts(self, request, pk=None):
        """Получение постов по хештегу"""
        hashtag = self.get_object()
        posts = Post.objects.filter(hashtags__hashtag=hashtag).order_by('-created_at')
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class TrendViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с трендами (только чтение)
    """
    queryset = Trend.objects.all().order_by('-trend_score')
    serializer_class = TrendSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Фильтрация трендов на основе параметров запроса
        """
        queryset = Trend.objects.all().order_by('-trend_score')
        
        # Получение параметров фильтрации из запроса
        category = self.request.query_params.get('category', None)
        location = self.request.query_params.get('location', None)
        
        if category is not None:
            queryset = queryset.filter(category=category)
        
        if location is not None:
            queryset = queryset.filter(location=location)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def categories(self, request):
        """Получение трендов по категориям"""
        categories = Trend.objects.values_list('category', flat=True).distinct()
        result = {}
        
        for category in categories:
            if category:  # Проверка на None и пустую строку
                trends = Trend.objects.filter(category=category).order_by('-trend_score')[:5]
                result[category] = TrendSerializer(trends, many=True).data
        
        return Response(result)
