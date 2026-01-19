# services/inventory_service.py
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List
from database import sqlite_connection

logger = logging.getLogger(__name__)

class InventoryService:
    """Сервис для работы с инвентаризацией"""
    
    @staticmethod
    def create_inventory_list(user_id: int, list_name: str = None) -> Optional[Dict]:
        """Создает новый список инвентаризации с датой проведения"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Если не передано имя, создаем автоматически
                if not list_name:
                    list_name = f"Инвентаризация от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                
                # Логируем начало операции
                logger.info(f"Создание списка для user_id={user_id}, name={list_name}")
                
                # 1. Сначала проверяем, существует ли пользователь в users
                # Пробуем найти по user_id (который может быть telegram_id)
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                user_exists = cursor.fetchone()
                
                if not user_exists:
                    # Пробуем найти по telegram_id (может быть то же самое)
                    cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (user_id,))
                    user_exists = cursor.fetchone()
                
                if not user_exists:
                    logger.warning(f"Пользователь {user_id} не найден, создаем...")
                    # Создаем пользователя без указания user_id (автоинкремент)
                    cursor.execute(
                        "INSERT INTO users (telegram_id, first_name, is_active) VALUES (?, 'User', 1)",
                        (user_id,)  # Используем user_id как telegram_id
                    )
                    # Получаем новый user_id из автоинкремента
                    new_user_id = cursor.lastrowid
                    logger.info(f"Создан новый пользователь: telegram_id={user_id}, user_id={new_user_id}")
                else:
                    new_user_id = user_exists['user_id']
                    logger.debug(f"Найден существующий пользователь: user_id={new_user_id}")
                
                # 2. Деактивируем старые активные списки пользователя
                cursor.execute(
                    "UPDATE inventory_lists SET is_active = 0 WHERE user_id = ? AND is_active = 1",
                    (new_user_id,)
                )
                logger.debug(f"Деактивировали старые списки для user_id={new_user_id}")
                
                # 3. Создаем новый список
                cursor.execute('''
                    INSERT INTO inventory_lists 
                    (user_id, list_name, created_at, inventory_date, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (
                    new_user_id,
                    list_name,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d')
                ))
                
                # Получаем ID созданной записи
                list_id = cursor.lastrowid
                logger.debug(f"Создан список с ID={list_id}")
                
                conn.commit()
                
                # 4. Теперь получаем созданную запись по ID
                cursor.execute('''
                    SELECT list_id, user_id, list_name, created_at, 
                           inventory_date, status, is_active
                    FROM inventory_lists 
                    WHERE list_id = ?
                ''', (list_id,))
                
                result = cursor.fetchone()
                
                if result:
                    result_dict = dict(result)
                    logger.info(f"Успешно создан список: {result_dict}")
                    return result_dict
                else:
                    logger.error(f"Список с ID={list_id} не найден после создания")
                    return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания списка инвентаризации: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_active_user_list(user_id: int) -> Optional[Dict]:
        """Получает активный список пользователя"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Сначала находим user_id в таблице users
                cursor.execute('''
                    SELECT u.user_id 
                    FROM users u 
                    WHERE u.user_id = ? OR u.telegram_id = ?
                    LIMIT 1
                ''', (user_id, user_id))
                
                user_record = cursor.fetchone()
                if not user_record:
                    logger.debug(f"Пользователь {user_id} не найден в таблице users")
                    return None
                
                actual_user_id = user_record['user_id']
                
                # Теперь ищем активный список
                cursor.execute('''
                    SELECT list_id, user_id, list_name, 
                           created_at, inventory_date, status, is_active
                    FROM inventory_lists
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (actual_user_id,))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                logger.debug(f"Активный список для user_id={actual_user_id} не найден")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения списка: {e}")
            return None
    
    @staticmethod
    def ensure_user_exists(telegram_id: int) -> Optional[int]:
        """Гарантирует, что пользователь существует в базе, возвращает user_id"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Пробуем найти пользователя по telegram_id
                cursor.execute(
                    "SELECT user_id FROM users WHERE telegram_id = ?",
                    (telegram_id,)
                )
                user = cursor.fetchone()
                
                if user:
                    logger.debug(f"Пользователь найден: telegram_id={telegram_id}, user_id={user['user_id']}")
                    return user['user_id']
                
                # Если не найден, создаем нового
                cursor.execute('''
                    INSERT INTO users (telegram_id, first_name, is_active)
                    VALUES (?, ?, 1)
                ''', (
                    telegram_id,
                    f"User_{telegram_id}"  # Имя пользователя по умолчанию
                ))
                
                new_user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Создан новый пользователь: telegram_id={telegram_id}, user_id={new_user_id}")
                return new_user_id
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания/поиска пользователя: {e}", exc_info=True)
            return None

    @staticmethod
    def add_item_to_list(list_id: int, name: str, quantity: float, unit: str, description: str = "") -> bool:
        """Добавляет товар в список инвентаризации"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем, существует ли уже такой товар в списке
                cursor.execute(
                    "SELECT item_id FROM inventory_items WHERE list_id = ? AND name = ?",
                    (list_id, name)
                )
                
                existing_item = cursor.fetchone()
                
                if existing_item:
                    # Обновляем существующий товар
                    cursor.execute('''
                        UPDATE inventory_items 
                        SET expected_quantity = expected_quantity + ?, 
                            updated_at = ?
                        WHERE item_id = ?
                    ''', (
                        quantity,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        existing_item['item_id']
                    ))
                else:
                    # Добавляем новый товар
                    cursor.execute('''
                        INSERT INTO inventory_items 
                        (list_id, name, description, expected_quantity, unit, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        list_id,
                        name,
                        description,
                        quantity,
                        unit,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления товара: {e}")
            return False
    
    @staticmethod
    def get_list_items(list_id: int) -> List[Dict]:
        """Получает все товары из списка"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT item_id, name, description, expected_quantity, unit, created_at
                    FROM inventory_items 
                    WHERE list_id = ?
                    ORDER BY name
                ''', (list_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения товаров списка: {e}")
            return []
    
    @staticmethod
    def clear_list(list_id: int) -> bool:
        """Очищает список товаров"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM inventory_items WHERE list_id = ?",
                    (list_id,)
                )
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка очистки списка: {e}")
            return False
    
    @staticmethod
    def deactivate_list(list_id: int) -> bool:
        """Деактивирует список инвентаризации"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE inventory_lists SET is_active = 0 WHERE list_id = ?",
                    (list_id,)
                )
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка деактивации списка: {e}")
            return False
    
    @staticmethod
    def get_user_lists(user_id: int) -> List[Dict]:
        """Получает все списки пользователя"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT list_id, list_name, created_at, is_active
                    FROM inventory_lists
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения списков пользователя: {e}")
            return []
    
    @staticmethod
    def get_list_by_date(user_id: int, date: str) -> Optional[Dict]:
        """Получает список инвентаризации по дате"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT list_id, list_name, created_at, is_active
                    FROM inventory_lists
                    WHERE user_id = ? AND DATE(created_at) = DATE(?)
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (user_id, date))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения списка по дате: {e}")
            return None

# Создаем экземпляр сервиса для импорта
inventory_service = InventoryService()