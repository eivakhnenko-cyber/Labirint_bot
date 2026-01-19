# handlers/reminder_manager.py
import logging
from datetime import datetime, time, timedelta
from typing import Optional, Dict, List, Any
import pytz
from telegram import Update
from telegram.ext import CallbackContext

from database import sqlite_connection
from keyboards.global_keyb import get_main_keyboard

logger = logging.getLogger(__name__)

class ReminderManager:
    """Класс для управления напоминаниями"""
    
    # Настройки по умолчанию
    DEFAULT_REMINDER_TIME = time(10, 0)  # 10:00
    DEFAULT_DAYS = [1, 3]  # Вторник и четверг
    LOCAL_TZ = pytz.timezone('Asia/Novosibirsk')
    
    REMINDER_TYPES = {
        "check_stock": "📦 Проверить остатки",
        "start_inventory": "🔄 Начать инвентаризацию",
        "custom": "➕ Свой вариант"
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ========== PUBLIC METHODS ==========
    
    async def setup_reminder_jobs(self, context: CallbackContext, user_id: int, chat_id: int) -> bool:
        """Создает задания для напоминаний в JobQueue"""
        try:
            self.logger.info(f"Настройка заданий для пользователя {user_id}")
            
            # Удаляем старые задания
            await self._remove_reminder_jobs(context, user_id)
            
            # Получаем настройки
            settings = await self._get_reminder_settings(user_id)
            if not settings:
                self.logger.error(f"Настройки не найдены для пользователя {user_id}")
                return False
            
            days = settings.get('days', self.DEFAULT_DAYS)
            reminder_time = settings.get('time', self.DEFAULT_REMINDER_TIME)
            
            # Конвертируем время в UTC
            utc_time = self._convert_to_utc(reminder_time)
            
            # Создаем задания для каждого дня
            for day in days:
                job_name = f"reminder_{user_id}_{day}"
                context.job_queue.run_daily(
                    callback=self.send_reminder_callback,
                    time=utc_time,
                    days=(day,),
                    data={'user_id': user_id, 'chat_id': chat_id},
                    name=job_name
                )
                self.logger.info(f"Создано задание: {job_name}")
            
            # Тестовое напоминание через 30 секунд
            context.job_queue.run_once(
                callback=self.send_reminder_callback,
                when=30,
                data={'user_id': user_id, 'chat_id': chat_id},
                name=f"test_reminder_{user_id}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания заданий: {e}", exc_info=True)
            return False
    
    async def send_reminder_callback(self, context: CallbackContext) -> None:
        """Callback функция для отправки напоминаний"""
        try:
            job = context.job
            if not job:
                self.logger.error("Job не найдена в контексте")
                return
            
            user_id = job.data.get('user_id')
            chat_id = job.data.get('chat_id')
            
            if not user_id or not chat_id:
                self.logger.error(f"Неверные данные: user_id={user_id}, chat_id={chat_id}")
                return
            
            await self._send_reminder_message(context, user_id, chat_id)
            
        except Exception as e:
            self.logger.error(f"Ошибка в callback: {e}", exc_info=True)
    
    async def save_reminder_settings(self, user_id: int, chat_id: int, enabled: bool) -> bool:
        """Сохраняет настройки напоминаний"""
        try:
            return await self._save_reminder_settings_db(user_id, chat_id, enabled)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек: {e}")
            return False
    
    async def get_reminder_status(self, user_id: int) -> Dict[str, Any]:
        """Получает статус и настройки напоминаний"""
        try:
            status = await self._get_reminders_status_db(user_id)
            settings = await self._get_reminder_settings(user_id)
            
            return {
                'status': status,
                'settings': settings,
                'status_text': "✅ Включены" if status else "❌ Выключены"
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса: {e}")
            return {'status': False, 'settings': None, 'status_text': "❌ Ошибка"}
    
    # ========== PRIVATE METHODS ==========
    
    def _convert_to_utc(self, local_time: time, for_today: bool = False) -> time:
        """Конвертирует локальное время в UTC с учётом текущего времени"""
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Конвертация времени: {local_time}, for_today: {for_today}")
            
            # Получаем текущую дату и время в локальном часовом поясе
            local_now = datetime.now(self.LOCAL_TZ)
            today = local_now.date()
            current_time = local_now.time()
            
            logger.info(f"Текущее локальное время: {current_time}, дата: {today}")
            
            # Определяем целевую дату
            if current_time >= local_time and not for_today:
                # Время уже прошло сегодня - используем завтра
                target_date = today + timedelta(days=1)
                logger.info(f"Время прошло, используем завтрашнюю дату: {target_date}")
            else:
                target_date = today
                logger.info(f"Используем сегодняшнюю дату: {target_date}")
            
            # Создаем datetime объект
            naive_dt = datetime.combine(target_date, local_time)
            logger.info(f"Naive datetime создан: {naive_dt}")
            
            # Локализуем в правильном часовом поясе
            local_dt = self.LOCAL_TZ.localize(naive_dt, is_dst=None)
            logger.info(f"Локализованный datetime: {local_dt}")
            
            # Конвертируем в UTC
            utc_dt = local_dt.astimezone(pytz.UTC)
            logger.info(f"UTC datetime: {utc_dt}")
            
            return utc_dt.time()
            
        except Exception as e:
            logger.error(f"Ошибка конвертации времени {local_time}: {e}", exc_info=True)
            # Возвращаем время по умолчанию
            return time(7, 0)  # 7:00 UTC соответствует 10:00 Новосибирск
    
    async def _send_reminder_message(self, context: CallbackContext, user_id: int, chat_id: int) -> None:
        """Отправляет сообщение напоминания"""
        try:
            message_text = await self._generate_reminder_text(user_id)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=await get_main_keyboard(user_id)
            )
            
            self.logger.info(f"Отправлено напоминание пользователю {user_id}")
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}", exc_info=True)
    
    async def _generate_reminder_text(self, user_id: int) -> str:
        """Генерирует текст напоминания с учетом типа"""
        reminder_type = await self._get_reminder_type_db(user_id)
        
        if reminder_type == 'check_stock':
            inventory_list = await self.get_user_inventory(user_id)
            
            if inventory_list:
                return (
                    "⏰ НАПОМИНАНИЕ: ПРОВЕРИТЬ ОСТАТКИ\n\n"
                    "Пора проверить наличие товаров:\n"
                    f"{inventory_list}\n\n"
                    "Используйте кнопку '✅ Подтвердить инвентаризацию' "
                    "после завершения проверки."
                )
            else:
                return (
                    "⏰ НАПОМИНАНИЕ: ПРОВЕРИТЬ ОСТАТКИ\n\n"
                    "Пора провести проверку остатков!\n\n"
                    "Ваш список товаров пуст. "
                    "Добавьте товары через меню '➕ Добавить товар'."
                )
                
        elif reminder_type == 'start_inventory':
            return (
                "🔄 НАПОМИНАНИЕ: НАЧАТЬ ИНВЕНТАРИЗАЦИЮ\n\n"
                "Пора начать полную инвентаризацию!\n\n"
                "Перейдите в меню инвентаризации для начала процесса."
            )
            
        elif reminder_type == 'custom':
            custom_text = await self.get_custom_reminder_text(user_id)
            if custom_text:
                return f"⏰ НАПОМИНАНИЕ:\n\n{custom_text}"
            else:
                return "⏰ НАПОМИНАНИЕ: Пора провести инвентаризацию!"
        else:
            return "⏰ НАПОМИНАНИЕ: Пора проверить остатки товаров!"
    
    async def _remove_reminder_jobs(self, context: CallbackContext, user_id: int) -> None:
        """Удаляет задания напоминаний"""
        try:
            if not context.application.job_queue:
                return
            
            jobs = context.application.job_queue.jobs()
            for job in jobs:
                if job.name and job.name.startswith(f"reminder_{user_id}_"):
                    job.schedule_removal()
                    
        except Exception as e:
            self.logger.error(f"Ошибка удаления заданий: {e}")
    
    # ========== DATABASE METHODS ==========
    
    async def _save_reminder_settings_db(self, user_id: int, chat_id: int, enabled: bool) -> bool:
        """Сохраняет настройки в БД"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO reminders 
                    (user_id, chat_id, is_active, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, chat_id, enabled))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения в БД: {e}")
            return False
    
    async def _get_reminders_status_db(self, user_id: int) -> bool:
        """Получает статус из БД"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT is_active FROM reminders WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result['is_active'] if result else False
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса из БД: {e}")
            return False
    
    async def _get_reminder_type_db(self, user_id: int) -> str:
        """Получает тип напоминания из БД"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT reminder_type FROM reminders WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result['reminder_type'] if result else 'check_stock'
        except Exception as e:
            self.logger.error(f"Ошибка получения типа из БД: {e}")
            return 'check_stock'
    
    async def _get_reminder_settings(self, user_id: int) -> Optional[Dict]:
        """Получает все настройки"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT days_of_week, reminder_time FROM reminders WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                settings = {}
                
                # Дни недели
                if result['days_of_week']:
                    try:
                        settings['days'] = [
                            int(day.strip()) 
                            for day in result['days_of_week'].split(',') 
                            if day.strip().isdigit()
                        ]
                    except:
                        settings['days'] = self.DEFAULT_DAYS
                
                # Время
                if result['reminder_time']:
                    try:
                        settings['time'] = datetime.strptime(
                            result['reminder_time'], "%H:%M:%S"
                        ).time()
                    except:
                        settings['time'] = self.DEFAULT_REMINDER_TIME
                
                return settings
                
        except Exception as e:
            self.logger.error(f"Ошибка получения настроек: {e}")
            return None
        
    async def get_user_inventory(self, user_id: int) -> str:
            """Получает список товаров пользователя для напоминания"""
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT i.name, i.expected_quantity, i.unit
                        FROM inventory_items i
                        JOIN inventory_lists l ON i.list_id = l.list_id
                        WHERE l.user_id = ? AND l.is_active = 1
                        ORDER BY i.name
                        LIMIT 10
                    ''', (user_id,))
                    
                    items = cursor.fetchall()
                    
                    if not items:
                        return ""
                    
                    return "\n".join([
                        f"• {item['name']} - {item['expected_quantity']} {item['unit']}"
                        for item in items
                    ])
                    
            except Exception as e:
                self.logger.error(f"Ошибка получения списка товаров: {e}")
                return ""
        
    async def save_reminder_days(self, user_id: int, days: list) -> bool:
            """Сохраняет дни напоминаний в БД"""
            try:
                days_str = ','.join(map(str, days))
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE reminders 
                        SET days_of_week = ?
                        WHERE user_id = ?
                    ''', (days_str, user_id))
                    conn.commit()
                    return True
                    
            except Exception as e:
                self.logger.error(f"Ошибка сохранения дней напоминаний: {e}")
                return False
        
    async def save_reminder_time(self, user_id: int, reminder_time: time) -> bool:
            """Сохраняет время напоминания в БД"""
            try:
                time_str = reminder_time.strftime("%H:%M:%S")
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Сначала создаем запись пользователя если её нет
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (user_id) 
                        VALUES (?)
                    ''', (user_id,))
                    
                    # Проверяем существование записи в reminders
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM reminders WHERE user_id = ?",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    
                    if result['count'] > 0:
                        cursor.execute('''
                            UPDATE reminders 
                            SET reminder_time = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        ''', (time_str, user_id))
                    else:
                        # Создаем полную запись с дефолтными значениями
                        cursor.execute('''
                            INSERT INTO reminders 
                            (user_id, reminder_time, is_active, days_of_week, reminder_type, chat_id)
                            VALUES (?, ?, 0, ?, ?, ?)
                        ''', (
                            user_id, 
                            time_str, 
                            "1,3",  # Дни по умолчанию
                            "check_stock",  # Тип по умолчанию
                            user_id  # chat_id по умолчанию = user_id
                        ))
                    
                    conn.commit()
                    return True

            except Exception as e:
                self.logger.error(f"Ошибка сохранения времени напоминания: {e}", exc_info=True)
                return False
        
    async def save_reminder_type(self, user_id: int, reminder_type: str) -> bool:
            """Сохраняет тип напоминания в БД"""
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE reminders 
                        SET reminder_type = ?
                        WHERE user_id = ?
                    ''', (reminder_type, user_id))
                    conn.commit()
                    return True
            except Exception as e:
                self.logger.error(f"Ошибка сохранения типа напоминания: {e}")
                return False
        
    async def save_custom_reminder(self, user_id: int, custom_text: str) -> bool:
            """Сохраняет custom текст напоминания в БД"""
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE reminders 
                        SET reminder_custom_text = ?, reminder_type = 'custom'
                        WHERE user_id = ?
                    ''', (custom_text, user_id))
                    conn.commit()
                    return True
            except Exception as e:
                self.logger.error(f"Ошибка сохранения custom напоминания: {e}")
                return False
        
    async def get_custom_reminder_text(self, user_id: int) -> str:
            """Получает custom текст напоминания из БД"""
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT reminder_custom_text FROM reminders WHERE user_id = ?",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    return result['reminder_custom_text'] if result and result['reminder_custom_text'] else ''
            except Exception as e:
                self.logger.error(f"Ошибка получения custom напоминания: {e}")
                return ''
        
    async def get_reminder_type_with_fallback(self, user_id: int) -> str:
            """Получает тип напоминания с fallback на default"""
            return await self._get_reminder_type_db(user_id)
        
    async def get_full_reminder_settings(self, user_id: int) -> Dict[str, Any]:
            """Получает полные настройки напоминания"""
            settings = await self._get_reminder_settings(user_id)
            reminder_type = await self._get_reminder_type_db(user_id)
            
            if settings:
                settings['type'] = reminder_type
                if reminder_type == 'custom':
                    settings['custom_text'] = await self.get_custom_reminder_text(user_id)
            
            return settings