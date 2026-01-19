import logging
from telegram import Update
from telegram.ext import CallbackContext
from typing import Dict, List, Optional
from enum import Enum
import random
import string
import decimal
from datetime import datetime
from database import sqlite_connection
from handlers.admin_roles_class import role_manager, Permission, UserRole
from keyboards.customeers_keyb import get_customers_main_keyboard, get_customers_purch_keyboard, get_customer_search_keyboard


logger = logging.getLogger(__name__)


class CustomerRegister:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def save_customer(self, update: Update, context: CallbackContext, customer_data: dict) -> None:
        """Сохранение клиента в БД"""
        operator_telegram_id = update.effective_user.id  # Telegram ID оператора
        
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Получаем или создаем пользователя (клиента) в таблице users
                # Для клиента не должно быть telegram_id, т.к. он не использует Telegram бота
                # Используем телефон как уникальный идентификатор
                cursor.execute('''
                    INSERT INTO users (
                        username, 
                        first_name,
                        created_at,
                        is_active,
                        telegram_id
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, ?, NULL)
                ''', (
                    customer_data['username'],
                    customer_data['username'],  # Используем username как first_name
                    1  # Активен по умолчанию
                ))
                
                user_id = cursor.lastrowid
                self.logger.info(f"Создан пользователь для клиента с user_id: {user_id}")
                
                # 2. Создаем запись в таблице user_roles для клиента
                cursor.execute('''
                    INSERT INTO user_roles (
                        user_id, 
                        role, 
                        created_at,
                        updated_at
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    UserRole.VISITOR.value
                ))
                self.logger.info(f"Установлена роль VISITOR для пользователя {user_id}")
                
                # 3. Создаем запись в таблице customers
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
                    customer_data['username'],
                    customer_data['phone'],
                    customer_data['birthday'],
                    customer_data['card_number'],
                    1  # Активен по умолчанию
                ))
                
                customer_id = cursor.lastrowid
                self.logger.info(f"Создан клиент с customer_id: {customer_id}")
                
                # 4. Назначаем дефолтную бонусную программу, если есть
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
                        self.logger.info(f"Назначена бонусная программа {default_program['program_id']} клиенту {customer_id}")
                except Exception as e:
                    self.logger.warning(f"Не удалось назначить бонусную программу: {e}")
                
                conn.commit()
                self.logger.info(f"Клиент {customer_id} успешно зарегистрирован оператором {operator_telegram_id}")
                
                del context.user_data['registering_customer']
                
                # Формируем итоговое сообщение
                message = (
                    f"✅ *Клиент успешно зарегистрирован!*\n\n"
                    f"👤 *Имя:* {customer_data['username']}\n"
                    f"📱 *Телефон:* {customer_data['phone']}\n"
                )
                
                if customer_data['birthday']:
                    # Преобразуем формат даты для отображения
                    try:
                        birth_date = datetime.strptime(customer_data['birthday'], "%Y-%m-%d")
                        message += f"🎂 *Дата рождения:* {birth_date.strftime('%d.%m.%Y')}\n"
                    except:
                        message += f"🎂 *Дата рождения:* {customer_data['birthday']}\n"
                
                message += (
                    f"💳 *Номер карты:* {customer_data['card_number']}\n"
                    f"🆔 *ID пользователя:* {user_id}\n"
                    f"🆔 *ID клиента:* {customer_id}\n"
                    f"📅 *Дата регистрации:* {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Карту можно использовать для начисления бонусов."
                )
                
                await update.message.reply_text(
                    message,
                    reply_markup=await get_customers_main_keyboard(),
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения клиента: {e}", exc_info=True)
            
            # Пытаемся откатить частичные изменения
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    # Удаляем частично созданные записи
                    if 'user_id' in locals():
                        cursor.execute('DELETE FROM customers WHERE user_id = ?', (user_id,))
                        cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
                        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                        conn.commit()
                        logger.info(f"Удалены частичные записи для user_id {user_id}")
            except Exception as cleanup_error:
                self.logger.error(f"Ошибка при очистке частичных данных: {cleanup_error}")
            
            await update.message.reply_text(
                f"❌ Ошибка при регистрации клиента: {str(e)}",
                reply_markup=await get_customers_main_keyboard()
            )

    def generate_card_number(self) -> str:
        """Генерация номера карты"""
        # Генерируем уникальный номер карты
        while True:
            prefix = "LBC"
            numbers = ''.join(random.choices(string.digits, k=12))
            card_number = f"{prefix}-{numbers[:4]}-{numbers[4:8]}-{numbers[8:12]}"
            
            # Проверяем уникальность
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT customer_id FROM customers WHERE card_number = ?",
                        (card_number,)
                    )
                    if not cursor.fetchone():
                        return card_number
            except Exception as e:
                self.logger.error(f"Ошибка проверки уникальности карты: {e}")
                return card_number
            
customer_register = CustomerRegister()