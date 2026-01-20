import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла переменные
load_dotenv()

# Получаем токен из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # 0 если не установлено
DATABASE_URL = os.getenv('DATABASE_URL', 'C:\\Documents\\Labirint_bot\\labirint.db')

# Проверка что токен установлен
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения!")