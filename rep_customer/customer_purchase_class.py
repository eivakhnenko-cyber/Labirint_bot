import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from typing import Dict, Optional
import decimal
from database import sqlite_connection
from config.buttons import Buttons
from keyboards.global_keyb import get_cancel_keyboard
from keyboards.bonus_keyb import get_confirm_bonus_keyboard
from keyboards.customeers_keyb import get_customers_main_keyboard

logger = logging.getLogger(__name__)


class CustomerPurchase:
    """Класс для управления покупками клиентов"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def find_customer_by_cardprogram(self, card_number: str) -> Optional[Dict]:
        """Найти клиента по номеру карты c программой"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.customer_id, c.username, c.card_number, 
                        c.total_purchases, c.bonus_program_id,
                        c.available_bonuses,
                        bp.base_percent
                    FROM customers c
                    LEFT JOIN bonus_programs bp ON c.bonus_program_id = bp.program_id
                    WHERE c.card_number = ? AND c.is_active = 1
                ''', (card_number,))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиента по карте {card_number}: {e}")
            raise

    def calculate_current_bonus_percent(self, total_purchases: decimal.Decimal, program_id: int = None) -> decimal.Decimal:
        """Рассчитывает текущий процент бонусов"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                if program_id:
                    # Получаем уровни программы
                    cursor.execute('''
                        SELECT bonus_percent, min_total_purchases
                        FROM bonus_levels
                        WHERE program_id = ?
                        ORDER BY min_total_purchases DESC
                    ''', (program_id,))
                    
                    levels = cursor.fetchall()
                    
                    for level in levels:
                        if total_purchases >= level['min_total_purchases']:
                            return decimal.Decimal(str(level['bonus_percent']))
                
                # Если программа не найдена или нет уровней, берем базовый процент
                cursor.execute('''
                    SELECT base_percent FROM bonus_programs 
                    WHERE program_id = ? AND is_active = 1
                ''', (program_id,))
                
                program = cursor.fetchone()
                if program:
                    return decimal.Decimal(str(program['base_percent']))
                
                # Дефолтный процент если нет программы
                return decimal.Decimal('3.0')
                
        except Exception as e:
            self.logger.error(f"Ошибка расчета процента бонусов: {e}")
            return decimal.Decimal('3.0')

    def calculate_bonus_amount(self, purchase_amount: decimal.Decimal, bonus_percent: decimal.Decimal) -> decimal.Decimal:
        """Рассчитать сумму бонусов"""
        return purchase_amount * bonus_percent / 100

    async def save_purchase_transaction(self, purchase_data: dict, operator_telegram_id: int) -> int:
        """Сохранение покупки в БД"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем user_id оператора
                cursor.execute('''
                    SELECT user_id FROM users 
                    WHERE telegram_id = ? AND is_active = 1
                ''', (operator_telegram_id,))
                
                operator_user = cursor.fetchone()
                
                if not operator_user:
                    raise ValueError(f"Оператор с telegram_id {operator_telegram_id} не найден")
                
                operator_id = operator_user['user_id']
                
                # Преобразуем decimal в float для SQLite
                amount = float(decimal.Decimal(purchase_data['amount']))
                bonus_amount = float(decimal.Decimal(purchase_data['bonus_amount']))
                
                # Сохраняем покупку
                cursor.execute('''
                    INSERT INTO customer_purchases (
                        customer_id, amount, bonus_earned, description, operator_id
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    purchase_data['customer']['customer_id'],
                    amount,
                    bonus_amount,
                    purchase_data.get('description'),
                    operator_id
                ))
                
                purchase_id = cursor.lastrowid
                
                # Обновляем статистику клиента
                cursor.execute('''
                    UPDATE customers 
                    SET total_purchases = total_purchases + ?,
                        total_bonuses = total_bonuses + ?,
                        available_bonuses = available_bonuses + ?
                    WHERE customer_id = ?
                ''', (
                    amount,
                    bonus_amount,
                    bonus_amount,
                    purchase_data['customer']['customer_id']
                ))
                
                # Сохраняем транзакцию бонусов
                cursor.execute('''
                    INSERT INTO bonus_transactions (
                        customer_id, purchase_id, bonus_amount, transaction_type, description
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    purchase_data['customer']['customer_id'],
                    purchase_id,
                    bonus_amount,
                    'earned',
                    f"Начисление за покупку {purchase_data['amount']} руб."
                ))
                
                conn.commit()
                return purchase_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения покупки: {e}")
            raise

    async def get_updated_customer_stats(self, customer_id: int) -> Dict:
        """Получить обновленную статистику клиента"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT total_purchases, available_bonuses 
                    FROM customers 
                    WHERE customer_id = ?
                ''', (customer_id,))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return {}
                
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики клиента: {e}")
            return {}


customer_purchase = CustomerPurchase()