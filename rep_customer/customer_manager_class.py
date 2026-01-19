# handlers/customer_manager_class.py
import logging
from typing import Dict, List, Optional
from datetime import datetime
import decimal
from database import sqlite_connection

logger = logging.getLogger(__name__)


class CustomerManager:
    """Класс для управления клиентами (бизнес-логика и запросы к БД)"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ============ ПОИСК КЛИЕНТОВ ============
    
    async def find_customers_by_search_query(self, search_query: str) -> List[Dict]:
        """Найти клиентов по поисковому запросу"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                query_pattern = f"%{search_query}%"
                
                cursor.execute('''
                    SELECT 
                        c.customer_id,
                        c.user_id,
                        c.username,
                        c.phone_number,
                        c.card_number,
                        c.birthday,
                        c.registration_date,
                        c.is_active,
                        c.total_purchases,
                        c.total_bonuses,
                        c.available_bonuses,
                        c.bonus_program_id,
                        bp.program_name,
                        bp.base_percent,
                        ur.role,
                        u.created_at as user_created_at
                    FROM customers c
                    LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                    LEFT JOIN users u ON c.user_id = u.user_id
                    LEFT JOIN user_roles ur ON c.user_id = ur.user_id
                    WHERE 
                        (c.card_number LIKE ? OR 
                         c.phone_number LIKE ? OR 
                         c.username LIKE ? OR
                         c.card_number = ? OR
                         c.phone_number = ?)
                        AND c.is_active = 1
                    ORDER BY c.customer_id DESC
                    LIMIT 10
                ''', (query_pattern, query_pattern, query_pattern, 
                      search_query, search_query))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиентов: {e}")
            raise
 
    async def find_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Найти клиента по ID"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        c.customer_id,
                        c.user_id,
                        c.username,
                        c.phone_number,
                        c.card_number,
                        c.birthday,
                        c.registration_date,
                        c.is_active,
                        c.total_purchases,
                        c.total_bonuses,
                        c.available_bonuses,
                        c.bonus_program_id,
                        bp.program_name,
                        bp.base_percent,
                        ur.role,
                        u.created_at as user_created_at
                    FROM customers c
                    LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                    LEFT JOIN users u ON c.user_id = u.user_id
                    LEFT JOIN user_roles ur ON c.user_id = ur.user_id
                    WHERE c.customer_id = ?
                ''', (customer_id,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиента по ID {customer_id}: {e}")
            raise

    async def find_customer_by_card(self, card_number: str) -> Optional[Dict]:
        """Найти клиента по номеру карты"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        c.customer_id,
                        c.user_id,
                        c.username,
                        c.phone_number,
                        c.card_number,
                        c.birthday,
                        c.registration_date,
                        c.is_active,
                        c.total_purchases,
                        c.total_bonuses,
                        c.available_bonuses,
                        c.bonus_program_id
                    FROM customers c
                    WHERE c.card_number = ? AND c.is_active = 1
                ''', (card_number,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиента по карте {card_number}: {e}")
            raise

    async def find_customer_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Найти клиента по Telegram ID"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        c.customer_id,
                        c.user_id,
                        c.username,
                        c.phone_number,
                        c.card_number,
                        c.birthday,
                        c.registration_date,
                        c.is_active,
                        c.total_purchases,
                        c.total_bonuses,
                        c.available_bonuses,
                        c.bonus_program_id,
                        bp.program_name,
                        bp.base_percent,
                        ur.role,
                        u.created_at as user_created_at
                    FROM users u
                    LEFT JOIN customers c ON u.user_id = c.user_id
                    LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                    LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                    WHERE u.telegram_id = ?
                ''', (telegram_id,))
                
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, result))
                #return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиента по Telegram ID {telegram_id}: {e}")
            return None

    async def find_customer_by_username_or_phone(self, username: str = None, phone: str = None) -> Optional[Dict]:
        """Найти клиента по имени или телефону"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        c.customer_id,
                        c.user_id,
                        c.username,
                        c.phone_number,
                        c.card_number,
                        c.birthday,
                        c.registration_date,
                        c.is_active,
                        c.total_purchases,
                        c.total_bonuses,
                        c.available_bonuses,
                        c.bonus_program_id,
                        bp.program_name,
                        bp.base_percent,
                        ur.role,
                        u.created_at as user_created_at
                    FROM customers c
                    LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                    LEFT JOIN users u ON c.user_id = u.user_id
                    LEFT JOIN user_roles ur ON c.user_id = ur.user_id
                    WHERE (c.phone_number = ? OR c.username LIKE ?)
                        AND c.is_active = 1
                    LIMIT 1
                ''', (phone, f"%{username}%" if username else ""))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиента по имени/телефону: {e}")
            return None

    # ============ СПИСКИ КЛИЕНТОВ ============
    
    async def get_all_customers(self, limit: int = 50) -> List[Dict]:
        """Получить всех активных клиентов"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                      SELECT 
                            c.customer_id,
                            c.user_id,
                            c.username,
                            c.phone_number,
                            c.card_number,
                            c.birthday,
                            c.registration_date,
                            c.is_active,
                            c.total_purchases,
                            c.total_bonuses,
                            c.available_bonuses,
                            c.bonus_program_id,
                            bp.program_name,
                            bp.base_percent,
                            ur.role,
                            u.created_at as user_created_at
                        FROM customers c
                        LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                        LEFT JOIN users u ON c.user_id = u.user_id
                        LEFT JOIN user_roles ur ON c.user_id = ur.user_id
                        WHERE c.is_active = 1
                        ORDER BY c.customer_id DESC
                        LIMIT ?
                    ''', (limit,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Ошибка получения списка клиентов: {e}")
            raise

    # ============ ПРОВЕРКИ И ВАЛИДАЦИИ ============
    
    async def is_phone_exists(self, phone: str) -> bool:
        """Проверить, существует ли клиент с таким номером телефона"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT customer_id FROM customers WHERE phone_number = ?",
                    (phone,)
                )
                return cursor.fetchone() is not None
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки номера телефона: {e}")
            return False
    
    async def is_card_exists(self, card_number: str) -> bool:
        """Проверить, существует ли клиент с таким номером карты"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT customer_id FROM customers WHERE card_number = ?",
                    (card_number,)
                )
                return cursor.fetchone() is not None
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки номера карты: {e}")
            return False

    # ============ ОБНОВЛЕНИЕ ДАННЫХ КЛИЕНТА ============
    
    async def update_customer_purchases(self, customer_id: int, amount: float, bonus_amount: float) -> bool:
        """Обновить сумму покупок и бонусов клиента"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE customers 
                    SET total_purchases = total_purchases + ?,
                        total_bonuses = total_bonuses + ?,
                        available_bonuses = available_bonuses + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                ''', (amount, bonus_amount, bonus_amount, customer_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления покупок клиента {customer_id}: {e}")
            return False

    async def update_customer_bonus_program(self, customer_id: int, program_id: int) -> bool:
        """Обновить бонусную программу клиента"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE customers 
                    SET bonus_program_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                ''', (program_id, customer_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления бонусной программы клиента {customer_id}: {e}")
            return False

    async def toggle_customer_status(self, customer_id: int) -> Optional[bool]:
        """Переключить статус активности клиента"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем текущий статус
                cursor.execute(
                    "SELECT is_active FROM customers WHERE customer_id = ?",
                    (customer_id,)
                )
                current = cursor.fetchone()
                
                if not current:
                    return None
                
                new_status = 0 if current['is_active'] else 1
                
                cursor.execute('''
                    UPDATE customers 
                    SET is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                ''', (new_status, customer_id))
                
                conn.commit()
                return bool(new_status)
                
        except Exception as e:
            self.logger.error(f"Ошибка переключения статуса клиента {customer_id}: {e}")
            return None

    # ============ СТАТИСТИКА И АНАЛИТИКА ============
    
    async def get_customer_statistics(self) -> Dict:
        """Получить общую статистику по клиентам"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_customers,
                        COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_customers,
                        SUM(total_purchases) as total_purchases,
                        SUM(available_bonuses) as total_available_bonuses,
                        SUM(total_bonuses) as total_issued_bonuses
                    FROM customers
                ''')
                
                stats = cursor.fetchone()
                return dict(stats) if stats else {}
                
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики клиентов: {e}")
            return {}
    
    async def get_top_customers(self, limit: int = 10) -> List[Dict]:
        """Получить топ клиентов по сумме покупок"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        customer_id,
                        username,
                        phone_number,
                        card_number,
                        total_purchases,
                        available_bonuses
                    FROM customers
                    WHERE is_active = 1
                    ORDER BY total_purchases DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Ошибка получения топ клиентов: {e}")
            raise


# Создаем экземпляр менеджера
customer_manager = CustomerManager()