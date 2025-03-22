from django.contrib import admin
from .models import Chat, Message, Attachment


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    """
    Административная панель для чатов
    """
    list_display = ('id', 'user1', 'user2', 'created_at', 'is_pinned')
    list_filter = ('is_pinned', 'created_at')
    search_fields = ('user1__username', 'user2__username')
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Административная панель для сообщений
    """
    list_display = ('id', 'chat', 'sender', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('content', 'sender__username')
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        """
        Превью содержимого сообщения (максимум 50 символов)
        """
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    
    content_preview.short_description = "Содержимое"


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """
    Административная панель для вложений
    """
    list_display = ('id', 'file_name', 'file_type', 'file_size_display', 'uploader', 'upload_date')
    list_filter = ('file_type', 'upload_date')
    search_fields = ('file_name', 'uploader__username')
    date_hierarchy = 'upload_date'
    
    def file_size_display(self, obj):
        """
        Отображение размера файла в человекочитаемом формате
        """
        size = obj.file_size
        
        if size < 1024:
            return f"{size} байт"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} КБ"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} МБ"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} ГБ"
    
    file_size_display.short_description = "Размер файла"