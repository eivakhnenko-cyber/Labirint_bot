import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN', '8335084468:AAFbc8MhiT4Hq_eSnHhYZs0yAEtkNCEg7YQ')
DB_PATH = 'C:\\Documents\\Labirint_bot\\labirint.db'