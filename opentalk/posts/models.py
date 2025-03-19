from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
import json


class Post(models.Model):
    """
    Модель поста пользователя
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name=_("Автор"))
    content = models.TextField(_("Содержание"))
    media_urls = models.TextField(_("Медиа"), blank=True, null=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)
    likes_count = models.PositiveIntegerField(_("Количество лайков"), default=0)
    reposts_count = models.PositiveIntegerField(_("Количество репостов"), default=0)
    comments_count = models.PositiveIntegerField(_("Количество комментариев"), default=0)
    is_repost = models.BooleanField(_("Репост"), default=False)
    original_post = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='reposts', verbose_name=_("Оригинальный пост"))
    
    class Meta:
        verbose_name = _("Пост")
        verbose_name_plural = _("Посты")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"
    
    def get_media_urls(self):
        if self.media_urls:
            return json.loads(self.media_urls)
        return []
    
    def set_media_urls(self, urls_list):
        self.media_urls = json.dumps(urls_list)


class Comment(models.Model):
    """
    Модель комментария к посту
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name=_("Пост"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name=_("Автор"))
    content = models.TextField(_("Содержание"))
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='replies', verbose_name=_("Родительский комментарий"))
    likes_count = models.PositiveIntegerField(_("Количество лайков"), default=0)
    
    class Meta:
        verbose_name = _("Комментарий")
        verbose_name_plural = _("Комментарии")
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} on {self.post}: {self.content[:30]}"


class Like(models.Model):
    """
    Модель лайка к посту или комментарию
    """
    CONTENT_TYPES = (
        ('post', 'Пост'),
        ('comment', 'Комментарий'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes', verbose_name=_("Пользователь"))
    content_type = models.CharField(_("Тип контента"), max_length=10, choices=CONTENT_TYPES)
    content_id = models.PositiveIntegerField(_("ID контента"))
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Лайк")
        verbose_name_plural = _("Лайки")
        unique_together = ('user', 'content_type', 'content_id')  # Пользователь может лайкнуть контент только один раз
    
    def __str__(self):
        return f"{self.user.username} likes {self.content_type} #{self.content_id}"


class Hashtag(models.Model):
    """
    Модель хештега
    """
    name = models.CharField(_("Название"), max_length=50, unique=True)
    post_count = models.PositiveIntegerField(_("Количество постов"), default=0)
    
    class Meta:
        verbose_name = _("Хештег")
        verbose_name_plural = _("Хештеги")
    
    def __str__(self):
        return f"#{self.name}"


class PostHashtag(models.Model):
    """
    Связь между постом и хештегом
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hashtags', verbose_name=_("Пост"))
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='posts', verbose_name=_("Хештег"))
    
    class Meta:
        verbose_name = _("Хештег поста")
        verbose_name_plural = _("Хештеги постов")
        unique_together = ('post', 'hashtag')  # Хештег может быть связан с постом только один раз
    
    def __str__(self):
        return f"{self.post.id} - {self.hashtag.name}"


class Trend(models.Model):
    """
    Модель тренда
    """
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='trends', verbose_name=_("Хештег"))
    trend_score = models.FloatField(_("Показатель популярности"))
    category = models.CharField(_("Категория"), max_length=50, blank=True)
    location = models.CharField(_("Местоположение"), max_length=100, blank=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Тренд")
        verbose_name_plural = _("Тренды")
        ordering = ['-trend_score']
    
    def __str__(self):
        return f"{self.hashtag.name} - {self.trend_score}"
