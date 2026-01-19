import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from database import sqlite_connection

logger = logging.getLogger(__name__)

class ReportWatchDB:
    """Класс для работы с отчетами о закрытии смены"""
    
    @staticmethod
    def create_report(user_id: int, username: str, phone_number: str, 
                     cash_morning: int, description: str = None) -> Optional[int]:
        """
        Создать новый отчет о смене
        
        Args:
            user_id: ID пользователя
            username: Имя пользователя
            phone_number: Телефон
            cash_morning: Сумма на начало смены
            description: Описание
            
        Returns:
            ID созданного отчета или None при ошибке
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Деактивируем предыдущие активные отчеты пользователя
                cursor.execute('''
                    UPDATE report_watchend 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND is_active = 1
                ''', (user_id,))
                
                # Создаем новый отчет
                cursor.execute('''
                    INSERT INTO report_watchend 
                    (user_id, username, phone_number, cash_morning, cash_rest, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, phone_number, cash_morning, cash_morning, description))
                
                report_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Создан отчет #{report_id} для пользователя {user_id}")
                return report_id
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания отчета: {e}")
            return None
    
    @staticmethod
    def add_expense(report_id: int, amount: int, description: str) -> bool:
        """
        Добавить запись расхода
        
        Args:
            report_id: ID отчета
            amount: Сумма расхода
            description: Описание расхода
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Добавляем расход
                cursor.execute('''
                    INSERT INTO report_expenses (report_id, cash_rested, description)
                    VALUES (?, ?, ?)
                ''', (report_id, amount, description))
                
                # Обновляем общую сумму расходов в основном отчете
                cursor.execute('''
                    UPDATE report_watchend 
                    SET cash_wasted = cash_wasted + ?,
                        cash_rest = cash_rest - ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE report_id = ?
                ''', (amount, amount, report_id))
                
                conn.commit()
                logger.info(f"Добавлен расход {amount} к отчету #{report_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления расхода: {e}")
            return False
    
    @staticmethod
    def update_cash_in(report_id: int, cash_in: int) -> bool:
        """
        Обновить приход наличных
        
        Args:
            report_id: ID отчета
            cash_in: Сумма прихода
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE report_watchend 
                    SET cash_in = ?,
                        cash_rest = cash_morning + ? - cash_wasted,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE report_id = ?
                ''', (cash_in, cash_in, report_id))
                
                conn.commit()
                logger.info(f"Обновлен приход {cash_in} для отчета #{report_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления прихода: {e}")
            return False
    
    @staticmethod
    def update_cash_online(report_id: int, cash_online: int) -> bool:
        """
        Обновить безналичный приход
        
        Args:
            report_id: ID отчета
            cash_online: Сумма безналичного прихода
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE report_watchend 
                    SET cash_online = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE report_id = ?
                ''', (cash_online, report_id))
                
                conn.commit()
                logger.info(f"Обновлен безнал {cash_online} для отчета #{report_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления безнала: {e}")
            return False
    
    @staticmethod
    def close_report(report_id: int, description: str = None) -> bool:
        """
        Закрыть отчет (деактивировать)
        
        Args:
            report_id: ID отчета
            description: Финальное описание
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE report_watchend 
                    SET is_active = 0,
                        description = COALESCE(?, description),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE report_id = ?
                ''', (description, report_id))
                
                conn.commit()
                logger.info(f"Закрыт отчет #{report_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка закрытия отчета: {e}")
            return False
    
    @staticmethod
    def get_active_report(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить активный отчет пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с данными отчета или None
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM report_watchend 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения активного отчета: {e}")
            return None
    
    @staticmethod
    def get_report_expenses(report_id: int) -> List[Dict[str, Any]]:
        """
        Получить все расходы отчета
        
        Args:
            report_id: ID отчета
            
        Returns:
            Список расходов
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM report_expenses 
                    WHERE report_id = ?
                    ORDER BY created_at
                ''', (report_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения расходов: {e}")
            return []
    
    @staticmethod
    def get_user_reports(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить последние отчеты пользователя
        
        Args:
            user_id: ID пользователя
            limit: Количество отчетов
            
        Returns:
            Список отчетов
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT r.*, 
                           (SELECT COUNT(*) FROM report_expenses e WHERE e.report_id = r.report_id) as expense_count
                    FROM report_watchend r
                    WHERE r.user_id = ?
                    ORDER BY r.created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения отчетов пользователя: {e}")
            return []
    
    @staticmethod
    def get_report_by_id(report_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить отчет по ID
        
        Args:
            report_id: ID отчета
            
        Returns:
            Словарь с данными отчета или None
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM report_watchend 
                    WHERE report_id = ?
                ''', (report_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения отчета по ID: {e}")
            return None
    
    @staticmethod
    def update_report_field(report_id: int, field: str, value: Any) -> bool:
        """
        Обновить поле отчета
        
        Args:
            report_id: ID отчета
            field: Поле для обновления
            value: Новое значение
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Специальная логика для некоторых полей
                if field == 'cash_morning':
                    cursor.execute('''
                        UPDATE report_watchend 
                        SET cash_morning = ?,
                            cash_rest = ? + cash_in - cash_wasted,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE report_id = ?
                    ''', (value, value, report_id))
                elif field == 'cash_in':
                    cursor.execute('''
                        UPDATE report_watchend 
                        SET cash_in = ?,
                            cash_rest = cash_morning + ? - cash_wasted,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE report_id = ?
                    ''', (value, value, report_id))
                elif field == 'cash_wasted':
                    cursor.execute('''
                        UPDATE report_watchend 
                        SET cash_wasted = ?,
                            cash_rest = cash_morning + cash_in - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE report_id = ?
                    ''', (value, value, report_id))
                else:
                    # Общее обновление для других полей
                    cursor.execute(f'''
                        UPDATE report_watchend 
                        SET {field} = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE report_id = ?
                    ''', (value, report_id))
                
                conn.commit()
                logger.info(f"Обновлено поле {field} отчета #{report_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления поля {field}: {e}")
            return False
    
    @staticmethod
    def get_daily_report(date: str = None) -> Dict[str, Any]:
        """
        Получить сводный отчет за день
        
        Args:
            date: Дата в формате YYYY-MM-DD (если None - текущий день)
            
        Returns:
            Словарь с суммарными данными
        """
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                if date:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as report_count,
                            SUM(cash_morning) as total_morning,
                            SUM(cash_wasted) as total_wasted,
                            SUM(cash_in) as total_in,
                            SUM(cash_online) as total_online,
                            SUM(cash_rest) as total_rest
                        FROM report_watchend 
                        WHERE DATE(created_at) = ? AND is_active = 0
                    ''', (date,))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as report_count,
                            SUM(cash_morning) as total_morning,
                            SUM(cash_wasted) as total_wasted,
                            SUM(cash_in) as total_in,
                            SUM(cash_online) as total_online,
                            SUM(cash_rest) as total_rest
                        FROM report_watchend 
                        WHERE DATE(created_at) = DATE('now') AND is_active = 0
                    ''')
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return {
                    'report_count': 0,
                    'total_morning': 0,
                    'total_wasted': 0,
                    'total_in': 0,
                    'total_online': 0,
                    'total_rest': 0
                }
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения дневного отчета: {e}")
            return {}