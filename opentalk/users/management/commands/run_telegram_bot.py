import logging
import asyncio
import threading
from django.core.management.base import BaseCommand
from django.core.management import call_command
from telegram import Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from django.conf import settings
import nest_asyncio

# Применяем nest_asyncio для поддержки вложенных циклов событий
nest_asyncio.apply()

# Настройки логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение настроек из Django settings
TELEGRAM_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
CHANNEL_ID = getattr(settings, 'TELEGRAM_CHANNEL_ID', '')

# Глобальная переменная для запущенного бота
bot_instance = None

class Command(BaseCommand):
    help = 'Запускает Django сервер и Telegram бота одновременно'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Запуск Django сервера и Telegram бота...')
        )
        
        # Запуск бота в отдельном потоке
        bot_thread = threading.Thread(target=self.run_bot)
        bot_thread.daemon = True  # Поток завершится вместе с основной программой
        bot_thread.start()
        
        # Запуск Django сервера
        call_command('runserver')

    def run_bot(self):
        """Запускает Telegram бота в отдельном потоке"""
        try:
            # Запускаем бота в цикле событий
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_bot())
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при запуске бота: {e}')
            )

    async def start_bot(self):
        """Инициализирует и запускает Telegram бота"""
        global bot_instance
        
        # Проверка наличия токена
        if not TELEGRAM_TOKEN:
            self.stdout.write(
                self.style.ERROR('Необходимо указать TELEGRAM_BOT_TOKEN в настройках Django')
            )
            return
        
        if not CHANNEL_ID:
            self.stdout.write(
                self.style.ERROR('Необходимо указать TELEGRAM_CHANNEL_ID в настройках Django')
            )
            return

        try:
            # Создание бота
            bot_instance = Bot(token=TELEGRAM_TOKEN)
            
            # Проверка соединения отправкой тестового сообщения
            await bot_instance.send_message(
                chat_id=CHANNEL_ID, 
                text="active"
            )
            
            # Создание приложения
            application = Application.builder().token(TELEGRAM_TOKEN).build()

            # Обработчики команд
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            
            # Обычные сообщения
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

            # Запуск бота
            self.stdout.write(self.style.SUCCESS('Telegram бот запущен успешно'))
            await application.run_polling(allowed_updates=["message"])
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка инициализации бота: {e}')
            )

    async def start_command(self, update, context):
        """Обработчик команды /start"""
        await update.message.reply_text("Бот для отправки кодов верификации запущен!")

    async def help_command(self, update, context):
        """Обработчик команды /help"""
        await update.message.reply_text(
            "Этот бот отправляет коды верификации в канал.\n"
            "Он интегрирован с Django и автоматически отправляет коды."
        )

    async def echo(self, update, context):
        """Эхо для обычных сообщений"""
        await update.message.reply_text(f"Получено: {update.message.text}")


# Метод для отправки кода подтверждения
# Будет вызываться из SendVerificationCodeSerializer
async def send_verification_code_to_telegram(phone, code):
    """
    Отправляет код подтверждения в Telegram канал
    
    Args:
        phone (str): Номер телефона
        code (str): Код подтверждения
    """
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        logging.error("Не указан TELEGRAM_BOT_TOKEN или TELEGRAM_CHANNEL_ID в settings.py")
        return
    
    try:
        # Форматирование номера телефона
        # Предполагаем, что номер в формате 79XXXXXXXXX
        formatted_phone = f"+7 (***) ***-{phone[-4:-2]}-{phone[-2:]}"
        
        # Форматирование сообщения
        message = f"{formatted_phone} - {code}"
        
        # Отправка сообщения
        # Если бот уже запущен и инициализирован, используем его
        if bot_instance:
            await bot_instance.send_message(chat_id=CHANNEL_ID, text=message)
        else:
            # Иначе создаем временный экземпляр бота
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=CHANNEL_ID, text=message, timeout=10)
        
        logging.info(f"Код подтверждения отправлен в Telegram канал: {message}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке кода в Telegram: {e}")
        return False


# Синхронная обертка для отправки сообщений
def send_code_to_telegram(phone, code):
    """
    Синхронная обертка для отправки кода в Telegram
    """
    try:
        # Используем nest_asyncio для предотвращения ошибок с циклами событий
        asyncio.run(send_verification_code_to_telegram(phone, code))
        return True
    except Exception as e:
        logging.error(f"Ошибка при вызове send_code_to_telegram: {e}")
        return False 