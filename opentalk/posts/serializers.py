from rest_framework import serializers
from .models import Post, Comment, Like, Hashtag, PostHashtag, Trend
from users.serializers import UserMiniSerializer


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для комментариев к постам
    """
    user = UserMiniSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'content', 'created_at', 'updated_at', 
            'parent', 'likes_count', 'is_liked'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'likes_count']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user, 
                content_type='comment', 
                content_id=obj.id
            ).exists()
        return False


class HashtagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для хештегов
    """
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'post_count']
        read_only_fields = ['id', 'post_count']


class PostSerializer(serializers.ModelSerializer):
    """
    Сериализатор для постов
    """
    user = UserMiniSerializer(read_only=True)
    media = serializers.SerializerMethodField(read_only=True)
    is_liked = serializers.SerializerMethodField(read_only=True)
    hashtags = serializers.SerializerMethodField(read_only=True)
    original_post_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'media', 'created_at', 'updated_at',
            'likes_count', 'reposts_count', 'comments_count', 'is_repost',
            'original_post', 'original_post_details', 'is_liked', 'hashtags'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 
                           'likes_count', 'reposts_count', 'comments_count']
    
    def get_media(self, obj):
        return obj.get_media_urls()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user, 
                content_type='post', 
                content_id=obj.id
            ).exists()
        return False
    
    def get_hashtags(self, obj):
        hashtags = Hashtag.objects.filter(
            posts__post=obj
        )
        return HashtagSerializer(hashtags, many=True).data
    
    def get_original_post_details(self, obj):
        """Возвращает детали оригинального поста, если это репост"""
        if obj.is_repost and obj.original_post:
            serializer = PostMinSerializer(obj.original_post, context=self.context)
            return serializer.data
        return None
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Обработка хештегов из контента
        content = validated_data.get('content', '')
        hashtags = []
        words = content.split()
        for word in words:
            if word.startswith('#') and len(word) > 1:
                hashtag_name = word[1:]  # Убираем символ # из начала
                if hashtag_name and not any(char in hashtag_name for char in " !@#$%^&*()+={}[]|\\:;\"'<>?,./"):
                    hashtags.append(hashtag_name.lower())
        
        # Обработка медиа, если они есть
        media_urls = self.context['request'].data.get('media', [])
        if media_urls:
            if isinstance(media_urls, str):
                try:
                    # Если прислана строка, пытаемся распарсить как JSON
                    import json
                    media_urls = json.loads(media_urls)
                except:
                    media_urls = [media_urls]
        
        post = Post.objects.create(
            user=user,
            **validated_data
        )
        
        # Сохраняем медиа
        if media_urls:
            post.set_media_urls(media_urls)
            post.save()
        
        # Сохраняем хештеги
        for tag in hashtags:
            hashtag, created = Hashtag.objects.get_or_create(name=tag)
            if created:
                hashtag.post_count = 1
            else:
                hashtag.post_count += 1
            hashtag.save()
            
            PostHashtag.objects.create(post=post, hashtag=hashtag)
        
        return post


class PostMinSerializer(serializers.ModelSerializer):
    """
    Упрощенный сериализатор поста для вложенных представлений
    """
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'created_at',
            'likes_count', 'reposts_count', 'comments_count'
        ]


class CreateCommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания комментария
    """
    class Meta:
        model = Comment
        fields = ['content', 'post', 'parent']
    
    def create(self, validated_data):
        user = self.context['request'].user
        comment = Comment.objects.create(
            user=user,
            **validated_data
        )
        
        # Увеличиваем счетчик комментариев в посте
        post = validated_data.get('post')
        post.comments_count += 1
        post.save()
        
        return comment


class LikeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для лайков
    """
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'content_type', 'content_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class TrendSerializer(serializers.ModelSerializer):
    """
    Сериализатор для трендов
    """
    hashtag = HashtagSerializer(read_only=True)
    
    class Meta:
        model = Trend
        fields = ['id', 'hashtag', 'trend_score', 'category', 'location', 'created_at']
        read_only_fields = ['id', 'created_at'] 