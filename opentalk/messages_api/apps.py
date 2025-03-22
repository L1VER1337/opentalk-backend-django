from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MessagesApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messages_api'
    verbose_name = _('Чаты и сообщения')