"""
Модуль для работы с данными бонусной системы.
Содержит все запросы к базе данных для бонусной системы.
"""
import logging
import decimal
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import sqlite_connection

logger = logging.getLogger(__name__)


class BonusDataManager:
    """Менеджер данных бонусной системы"""
    def __init__(self):
        self.logger = logging.getLogger(__name__) 

    @staticmethod
    def get_customer_bonus_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных клиента для бонусной системы"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        c.customer_id, 
                        c.username, 
                        c.card_number, 
                        c.total_purchases, 
                        c.total_bonuses,
                        c.available_bonuses,
                        c.bonus_program_id,
                        bp.base_percent,
                        bp.program_name,
                        -- Подсчет количества покупок из таблицы customer_purchases
                        COALESCE(COUNT(cp.purchase_id), 0) as purchase_count,
                        -- Сумма использованных бонусов
                        COALESCE(SUM(CASE 
                            WHEN bt.transaction_type = 'spent' 
                            THEN bt.bonus_amount 
                            ELSE 0 
                        END), 0) as spent_bonuses
                    FROM customers c
                    LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                    LEFT JOIN customer_purchases cp ON c.customer_id = cp.customer_id
                    LEFT JOIN bonus_transactions bt ON c.customer_id = bt.customer_id
                    LEFT JOIN users u ON c.user_id = u.user_id
                    WHERE u.user_id = ? AND c.is_active = 1
                    GROUP BY c.customer_id
                ''', (user_id,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"Ошибка получения данных клиента: {e}")
            return None
    
    @staticmethod
    def check_program_name_exists(self, program_name: str) -> bool:
        """Проверка существования программы с таким названием"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT program_id FROM bonus_programs WHERE program_name = ?",
                    (program_name,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Ошибка проверки названия программы: {e}")
            return False
    
    @staticmethod
    def save_bonus_program(self, program_data: Dict[str, Any], created_by: int) -> Optional[int]:
        """Сохранение бонусной программы в БД"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO bonus_programs (
                        program_name, description, base_percent, 
                        min_purchase_amount, created_by, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    program_data['name'],
                    program_data['description'],
                    program_data['base_percent'],
                    program_data['min_amount'],
                    created_by,
                    1  # Активна по умолчанию
                ))
                
                program_id = cursor.lastrowid
                
                # Создаем базовый уровень программы
                cursor.execute('''
                    INSERT INTO bonus_levels (
                        program_id, level_name, min_total_purchases, bonus_percent, description
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    program_id,
                    "Базовый",
                    "0",
                    program_data['base_percent'],
                    "Базовый уровень бонусной программы"
                ))
                
                conn.commit()
                return program_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения бонусной программы: {e}")
            return None
    
    @staticmethod
    def get_all_bonus_programs(self) -> List[Dict[str, Any]]:
        """Получение списка всех бонусных программ"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT program_id, program_name, description, 
                           base_percent, is_active
                    FROM bonus_programs
                    ORDER BY program_id
                ''')
                
                programs = cursor.fetchall()
                return [dict(program) for program in programs]
                
        except Exception as e:
            self.logger.error(f"Ошибка получения списка программ: {e}")
            return []
    
    @staticmethod
    def get_active_bonus_programs(self) -> List[Dict[str, Any]]:
        """Получение списка активных бонусных программ"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT program_id, program_name 
                    FROM bonus_programs 
                    WHERE is_active = 1
                    ORDER BY program_id
                ''')
                
                programs = cursor.fetchall()
                return [dict(program) for program in programs]
                
        except Exception as e:
            self.logger.error(f"Ошибка получения активных программ: {e}")
            return []
    
    @staticmethod
    def assign_program_to_all_customers(self, program_id: int) -> bool:
        """Назначение бонусной программы всем клиентам"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем клиентов без программы или с другой программой
                cursor.execute('''
                    UPDATE customers 
                    SET bonus_program_id = ? 
                    WHERE is_active = 1 AND bonus_program_id IS NULL
                ''', (program_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Ошибка назначения программы клиентам: {e}")
            return False

# Создаем экземпляр менеджера для использования
bonus_data_manager = BonusDataManager()