import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from database import sqlite_connection
from models.customer_models import CustomerDTO, CustomerRegistrationDTO

logger = logging.getLogger(__name__)

class CustomerRepository:
    """Репозиторий для работы с клиентами в БД"""
    
    @staticmethod
    def is_phone_registered(phone: str) -> bool:
        """Проверяет, зарегистрирован ли номер телефона"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT customer_id FROM customers WHERE phone_number = ?",
                    (phone,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки номера телефона: {e}")
            return False
    
    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по Telegram ID"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, phone_numb
                    FROM users 
                    WHERE telegram_id = ?
                ''', (telegram_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    @staticmethod
    def update_user_for_customer(telegram_id: int, username: str, 
                                first_name: str, phone: str) -> Optional[int]:
        """Обновляет запись пользователя для клиента и возвращает user_id"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Обновляем пользователя
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, 
                        first_name = ?,
                        phone_numb = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (username, first_name, phone, telegram_id))
                
                # Получаем user_id
                cursor.execute('SELECT user_id FROM users WHERE telegram_id = ?', 
                             (telegram_id,))
                row = cursor.fetchone()
                
                return row['user_id'] if row else None
                
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя: {e}")
            return None
    
    @staticmethod
    def update_user_role(user_id: int, role: str) -> bool:
        """Обновляет роль пользователя"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_roles 
                    SET role = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (role, user_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка обновления роли пользователя: {e}")
            return False
    
    @staticmethod
    def create_customer(user_id: int, username: str, phone: str, 
                       birthday: Optional[str], card_number: str) -> Optional[int]:
        """Создает запись клиента и возвращает customer_id"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO customers (
                        user_id, 
                        username, 
                        phone_number, 
                        birthday, 
                        card_number, 
                        registration_date,
                        is_active,
                        total_purchases,
                        total_bonuses,
                        available_bonuses
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 0, 0, 0)
                ''', (
                    user_id,
                    username,
                    phone,
                    birthday,
                    card_number,
                    1  # Активен
                ))
                
                customer_id = cursor.lastrowid
                
                # Назначаем дефолтную бонусную программу
                CustomerRepository._assign_default_bonus_program(cursor, customer_id)
                
                conn.commit()
                return customer_id
                
        except Exception as e:
            logger.error(f"Ошибка создания клиента: {e}")
            return None
    
    @staticmethod
    def _assign_default_bonus_program(cursor, customer_id: int) -> None:
        """Назначает дефолтную бонусную программу клиенту"""
        try:
            cursor.execute('''
                SELECT program_id FROM bonus_programs 
                WHERE is_active = 1 
                ORDER BY program_id LIMIT 1
            ''')
            default_program = cursor.fetchone()
            
            if default_program:
                cursor.execute('''
                    UPDATE customers 
                    SET bonus_program_id = ? 
                    WHERE customer_id = ?
                ''', (default_program['program_id'], customer_id))
        except Exception as e:
            logger.warning(f"Не удалось назначить бонусную программу: {e}")
    
    @staticmethod
    def is_card_number_unique(card_number: str) -> bool:
        """Проверяет уникальность номера карты"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT customer_id FROM customers WHERE card_number = ?",
                    (card_number,)
                )
                return cursor.fetchone() is None
        except Exception as e:
            logger.error(f"Ошибка проверки уникальности карты: {e}")
            return True
    
    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
        """Получает клиента по ID"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM customers 
                    WHERE customer_id = ?
                ''', (customer_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения клиента: {e}")
            return None
        
    @staticmethod
    def create_customer_dto(self, customer_data: CustomerRegistrationDTO) -> Optional[CustomerDTO]:
        """Создает клиента из DTO и возвращает CustomerDTO"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Преобразуем DTO в данные для БД
                birthday_db = customer_data.birthday
                if birthday_db and isinstance(birthday_db, datetime):
                    birthday_db = birthday_db.strftime("%Y-%m-%d")
                
                cursor.execute('''
                    INSERT INTO customers (
                        user_id, 
                        username, 
                        phone_number, 
                        birthday, 
                        card_number, 
                        registration_date,
                        is_active,
                        total_purchases,
                        total_bonuses,
                        available_bonuses
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 0, 0, 0)
                ''', (
                    customer_data.user_id,
                    customer_data.username,
                    customer_data.phone,
                    birthday_db,
                    customer_data.card_number,
                    1
                ))
                
                customer_id = cursor.lastrowid
                
                # Получаем созданного клиента
                cursor.execute('SELECT * FROM customers WHERE customer_id = ?', 
                             (customer_id,))
                row = cursor.fetchone()
                
                if row:
                    return CustomerDTO.from_db_row(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Ошибка создания клиента из DTO: {e}")
            return None