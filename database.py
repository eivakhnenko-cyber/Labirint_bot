import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

def init_db():
    """Инициализация базы данных"""
    try:
        with sqlite_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone_numb TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    language_code TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    reminders_enabled BOOLEAN DEFAULT 0,
                    reminder_chat_id INTEGER,
                    reminder_days TEXT,
                    reminder_time TIME DEFAULT '10:00'
                )
            ''')
            # Таблица клиентов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    username TEXT NOT NULL,
                    phone_number TEXT NOT NULL UNIQUE,
                    email TEXT,
                    birthday DATE,
                    first_name TEXT,
                    last_name TEXT,
                    card_number TEXT UNIQUE,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    bonus_program_id INTEGER,
                    total_purchases DECIMAL(10, 2) DEFAULT 0,
                    total_bonuses DECIMAL(10, 2) DEFAULT 0,
                    available_bonuses DECIMAL(10, 2) DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (bonus_program_id) REFERENCES bonus_programs(program_id)
                )
            ''')
            
            # Таблица бонусных программ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bonus_programs (
                    program_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    program_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    base_percent DECIMAL(5, 2) NOT NULL,
                    min_purchase_amount DECIMAL(10, 2) DEFAULT 0,
                    max_purchase_amount DECIMAL(10, 2),
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица уровней бонусной программы
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bonus_levels (
                    level_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    program_id INTEGER NOT NULL,
                    level_name TEXT NOT NULL,
                    min_total_purchases DECIMAL(10, 2) NOT NULL,
                    bonus_percent DECIMAL(5, 2) NOT NULL,
                    description TEXT,
                    FOREIGN KEY (program_id) REFERENCES bonus_programs(program_id)
                )
            ''')
            
            # Таблица транзакций (покупок)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    bonus_earned DECIMAL(10, 2) NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    operator_id INTEGER,
                    purchase_count INTEGER,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (operator_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица использования бонусов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bonus_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    purchase_id INTEGER,
                    bonus_amount DECIMAL(10, 2) NOT NULL,
                    transaction_type TEXT CHECK(transaction_type IN ('earned', 'spent', 'expired')) NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (purchase_id) REFERENCES customer_purchases(purchase_id)
                )
            ''')
            # Таблица пользователей и их ролей
            cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_roles (
                        user_id INTEGER PRIMARY KEY,
                        role TEXT NOT NULL DEFAULT 'barista',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
            ''')
            # Создаем таблицу reminders
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,  -- UNIQUE чтобы у каждого пользователя была только одна запись
                    chat_id INTEGER,
                    is_active BOOLEAN DEFAULT 0,
                    reminder_time TIME DEFAULT '10:00:00',
                    days_of_week TEXT DEFAULT '1,3',
                    reminder_type TEXT DEFAULT 'check_stock',
                    reminder_custom_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            # Таблица списков инвентаризации
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory_lists (
                    list_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(user_id),
                    list_name TEXT DEFAULT 'Основной список',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    inventory_date DATE,  -- Специальная дата проведения инвентаризации
                    status TEXT DEFAULT 'active',  -- active, completed, cancelled
                    completed_at TIMESTAMP,
                    completed_by INTEGER REFERENCES users(user_id),
                    is_active BOOLEAN DEFAULT 1,
                    UNIQUE(user_id, list_name)
                )
            ''')
            # Добавим триггер для автоматической установки inventory_date
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS set_inventory_date 
                AFTER INSERT ON inventory_lists
                BEGIN
                    UPDATE inventory_lists 
                    SET inventory_date = DATE(created_at)
                    WHERE list_id = NEW.list_id;
                END;
            ''')
            
            # Таблица товаров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_id INTEGER REFERENCES inventory_lists(list_id),
                    name TEXT NOT NULL,
                    description TEXT,
                    expected_quantity REAL DEFAULT 1,
                    unit TEXT DEFAULT 'шт',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(list_id, name)
                )
            ''')

            #каталог товаров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_catalog (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL UNIQUE,
                    unit TEXT DEFAULT 'шт',
                    default_quantity REAL DEFAULT 1,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # отчет основной по закрытию смены
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS report_watchend (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    phone_number TEXT NOT NULL,
                    username TEXT NOT NULL,
                    cash_morning INTEGER NOT NULL,
                    cash_wasted INTEGER DEFAULT 0,
                    cash_online INTEGER DEFAULT 0,
                    cash_in INTEGER DEFAULT 0,
                    cash_rest INTEGER NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Вспомогательная таблица для нескольких записей расхода
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS report_expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER NOT NULL,
                    cash_rested INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES report_watchend(report_id) ON DELETE CASCADE
                )
            ''')

            # Создаем индекс для быстрого поиска активных отчетов пользователя
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_report_user_active 
                ON report_watchend(user_id, is_active)
            ''')

            conn.commit()
            logger.info("База данных инициализирована")
            
    except sqlite3.Error as e:
        logger.error(f"Ошибка инициализации БД: {e}")

@contextmanager
def sqlite_connection(db_path='D:\\Documents\\Labirint_bot\\labirint.db'):
    """Контекстный менеджер для соединения c SQLite"""
    conn = None
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()

    except sqlite3.Error as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        if conn:
            conn.rollback()  # Откатываем изменения при ошибке
        raise
    finally:
        if conn:
            conn.close()