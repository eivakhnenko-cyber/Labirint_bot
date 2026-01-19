import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .report_watch_class import ReportWatchDB
from database import sqlite_connection

logger = logging.getLogger(__name__)

class ReportWatchManager:
    """Менеджер для работы с отчетами о смене"""
    
    def __init__(self):
        self.db = ReportWatchDB()
    
    async def start_new_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать новый отчет о смене"""
        user_id = update.effective_user.id
        
        # Получаем данные пользователя
        user_info = self._get_user_info(user_id)
        if not user_info:
            await update.message.reply_text("❌ Не удалось получить данные пользователя")
            return
        
        # Проверяем активный отчет
        active_report = self.db.get_active_report(user_id)
        if active_report:
            keyboard = [
                [InlineKeyboardButton("🔄 Продолжить текущий", callback_data=f"report_continue_{active_report['report_id']}")],
                [InlineKeyboardButton("📝 Начать новый", callback_data=f"report_new_{user_id}")],
                [InlineKeyboardButton("🔙 Выход", callback_data=f"exit_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"📊 У вас есть активный отчет от {active_report['created_at']}\n"
                f"Начальная сумма: {active_report['cash_morning']} ₽\n"
                f"Текущий остаток: {active_report['cash_rest']} ₽\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
            return
        
        # Запрашиваем начальную сумму
        context.user_data['creating_report'] = True
        context.user_data['report_user_info'] = user_info
        
        await update.message.reply_text(
            f"📝 Начало новой смены\n"
            f"Бариста: {user_info['username']}\n"
            f"Телефон: {user_info.get('phone_number', 'не указан')}\n\n"
            "Введите сумму наличных в кассе на начало смены (в рублях):"
        )
    
    def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.user_id, u.username, u.phone_numb as phone_number
                    FROM users u
                    WHERE u.user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения данных пользователя: {e}")
            return None
    
    async def process_cash_morning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать ввод начальной суммы"""
        try:
            cash_morning = int(update.message.text)
            if cash_morning < 0:
                await update.message.reply_text("❌ Сумма не может быть отрицательной")
                return
            
            user_info = context.user_data.get('report_user_info')
            if not user_info:
                await update.message.reply_text("❌ Ошибка: данные пользователя не найдены")
                return
            
            # Создаем отчет
            report_id = self.db.create_report(
                user_id=user_info['user_id'],
                username=user_info['username'],
                phone_number=user_info.get('phone_number', ''),
                cash_morning=cash_morning
            )
            
            if report_id:
                # Очищаем контекст
                context.user_data.pop('creating_report', None)
                context.user_data.pop('report_user_info', None)
                context.user_data['active_report_id'] = report_id
                
                keyboard = [
                    [InlineKeyboardButton("➕ Добавить расход", callback_data=f"report_add_expense_{report_id}")],
                    [InlineKeyboardButton("💰 Внести приход", callback_data=f"report_add_cash_{report_id}")],
                    [InlineKeyboardButton("💳 Безналичные", callback_data=f"report_add_online_{report_id}")],
                    [InlineKeyboardButton("📊 Показать отчет", callback_data=f"report_show_{report_id}")],
                    [InlineKeyboardButton("✅ Закрыть смену", callback_data=f"report_close_{report_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ Отчет создан! ID: #{report_id}\n"
                    f"Начальная сумма: {cash_morning} ₽\n\n"
                    "Используйте кнопки для управления отчетом:",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Ошибка создания отчета")
                
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите число")
        except Exception as e:
            logger.error(f"Ошибка обработки начальной суммы: {e}")
            await update.message.reply_text("❌ Произошла ошибка")
    
    async def add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: int):
        """Добавить расход"""
         # Проверяем тип update
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        
        context.user_data['adding_expense'] = True
        context.user_data['expense_report_id'] = report_id
        
        text = "📝 Добавление расхода\nВведите сумму и описание расхода через тире (-)\nНапример: 1500 - Закупка кофе"
    
        if hasattr(update, 'callback_query'):
            await query.edit_message_text(text)
        else:
            await message.reply_text(text)

    async def process_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать ввод расхода"""
        try:
            text = update.message.text.strip()
            if ' - ' in text:
                amount_str, description = text.split(' - ', 1)
            elif '-' in text:
                amount_str, description = text.split('-', 1)
            else:
                await update.message.reply_text("❌ Используйте формат: сумма - описание")
                return
            
            amount = int(amount_str.strip())
            description = description.strip()
            
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть положительной")
                return
            
            report_id = context.user_data.get('expense_report_id')
            if not report_id:
                await update.message.reply_text("❌ Отчет не найден")
                return
            
            # Добавляем расход
            success = self.db.add_expense(report_id, amount, description)
            
            if success:
                # Очищаем контекст
                context.user_data.pop('adding_expense', None)
                context.user_data.pop('expense_report_id', None)
                
                # Показываем обновленный отчет - ИСПРАВЛЕНО!
                # Вместо вызова show_report, который может вызвать ошибку,
                # напрямую вызываем _show_report_message
                await self._show_report_message(update, report_id, is_message=True)
            else:
                await update.message.reply_text("❌ Ошибка добавления расхода")
                
        except ValueError:
            await update.message.reply_text("❌ Неверный формат суммы")
        except Exception as e:
            logger.error(f"Ошибка обработки расхода: {e}")
            await update.message.reply_text("❌ Произошла ошибка")
    
    async def add_cash_in(self, update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: int):
        """Добавить приход наличных"""
        # Проверяем тип update
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        context.user_data['adding_cash_in'] = True
        context.user_data['cash_in_report_id'] = report_id
        
        text = "💰 Внесение наличных\nВведите сумму наличных, поступивших за смену:"

        if hasattr(update, 'callback_query'):
            await query.edit_message_text(text)
        else:
            await message.reply_text(text)
    
    async def process_cash_in(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать ввод прихода"""
        try:
            cash_in = int(update.message.text)
            if cash_in < 0:
                await update.message.reply_text("❌ Сумма не может быть отрицательной")
                return
            
            report_id = context.user_data.get('cash_in_report_id')
            if not report_id:
                await update.message.reply_text("❌ Отчет не найден")
                return
            
            # Обновляем приход
            success = self.db.update_cash_in(report_id, cash_in)
            
            if success:
                # Очищаем контекст
                context.user_data.pop('adding_cash_in', None)
                context.user_data.pop('cash_in_report_id', None)
                
                # Показываем обновленный отчет
                await self._show_report_message(update, report_id, is_message=True)
            else:
                await update.message.reply_text("❌ Ошибка обновления прихода")
                
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите число")
        except Exception as e:
            logger.error(f"Ошибка обработки прихода: {e}")
            await update.message.reply_text("❌ Произошла ошибка")
    
    async def add_online_cash(self, update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: int):
        """Добавить безналичный приход"""
        # Проверяем тип update
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        context.user_data['adding_online'] = True
        context.user_data['online_report_id'] = report_id
        
        text = "💳 Безналичные поступления\nВведите сумму безналичных платежей за смену:"
        
        if hasattr(update, 'callback_query'):
            await query.edit_message_text(text)
        else:
            await message.reply_text(text)
    
    async def process_online_cash(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать ввод безналичных"""
        try:
            cash_online = int(update.message.text)
            if cash_online < 0:
                await update.message.reply_text("❌ Сумма не может быть отрицательной")
                return
            
            report_id = context.user_data.get('online_report_id')
            if not report_id:
                await update.message.reply_text("❌ Отчет не найден")
                return
            
            # Обновляем безналичные
            success = self.db.update_cash_online(report_id, cash_online)
            
            if success:
                # Очищаем контекст
                context.user_data.pop('adding_online', None)
                context.user_data.pop('online_report_id', None)
                
                # Показываем обновленный отчет - ИСПРАВЛЕНО!
                await self._show_report_message(update, report_id, is_message=True)
            else:
                await update.message.reply_text("❌ Ошибка обновления безналичных")
                
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите число")
        except Exception as e:
            logger.error(f"Ошибка обработки безналичных: {e}")
            await update.message.reply_text("❌ Произошла ошибка")
    
    async def show_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: int = None):
        """Показать отчет"""
        if not report_id:
            report_id = context.user_data.get('active_report_id')
            if not report_id:
                # Пытаемся найти активный отчет пользователя
                user_id = update.effective_user.id
                active_report = self.db.get_active_report(user_id)
                if active_report:
                    report_id = active_report['report_id']
                else:
                    if hasattr(update, 'callback_query'):
                        await update.callback_query.message.reply_text("📭 У вас нет активных отчетов")
                    else:
                        await update.message.reply_text("📭 У вас нет активных отчетов")
                    return
        # Определяем тип обновления - ДОБАВЛЕНО!
        is_message = hasattr(update, 'message') and not hasattr(update, 'callback_query')
        await self._show_report_message(update, report_id, is_message)

    
    async def close_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: int):
        """Закрыть отчет"""
        query = update.callback_query
        await query.answer()
        
        # Закрываем отчет
        success = self.db.close_report(report_id, "Смена закрыта")
        
        if success:
            # Очищаем активный отчет из контекста
            context.user_data.pop('active_report_id', None)
            
            await query.edit_message_text(
                f"✅ Смена закрыта!\n"
                f"Отчет #{report_id} сохранен в истории."
            )
        else:
            await query.edit_message_text("❌ Ошибка закрытия отчета")
    
    async def show_report_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
        """Показать историю отчетов"""
        if not user_id:
            user_id = update.effective_user.id
        
        # Определяем тип обновления
        if hasattr(update, 'callback_query') and update.callback_query is not None:
            is_callback = True
            message_obj = update.callback_query.message
        else:
            is_callback = False
            message_obj = update.message
        
        # Получаем отчеты пользователя
        reports = self.db.get_user_reports(user_id, limit=5)
        
        if not reports:
            keyboard = [
                [InlineKeyboardButton("📝 Начать новую смену", callback_data=f"report_new_{user_id}")]
            ]
        
        # Если это callback из меню отчетности, добавляем кнопку назад
            if 'active_report_id' in context.user_data:
                keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"report_show_{context.user_data['active_report_id']}")])
            else:
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "📭 У вас еще нет отчетов"
            
            if is_callback:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await message_obj.reply_text(text, reply_markup=reply_markup)
            return
        
        message = "📋 ИСТОРИЯ ОТЧЕТОВ\n\n"
        
        for report in reports:
            status = "🟢 Активна" if report['is_active'] else "🔴 Закрыта"
            message += f"#{report['report_id']} - {report['created_at']} - {status}\n"
            message += f"  Начало: {report['cash_morning']} ₽ | "
            message += f"Расход: {report['cash_wasted']} ₽ | "
            message += f"Приход: {report['cash_in']} ₽\n"
            message += f"  Безнал: {report['cash_online']} ₽ | "
            message += f"Остаток: {report['cash_rest']} ₽\n"
            
            if report['expense_count'] > 0:
                message += f"  Расходов: {report['expense_count']}\n"
            
            message += "─" * 40 + "\n"
        
        # Создаем клавиатуру
        keyboard = []
        for report in reports:
            created_date = report['created_at'][:10] if isinstance(report['created_at'], str) else report['created_at']
            status_icon = "🟢" if report['is_active'] else "🔴"
            keyboard.append([InlineKeyboardButton(
                f"{status_icon} #{report['report_id']} - {created_date}", 
                callback_data=f"report_show_{report['report_id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("📝 Новая смена", callback_data=f"report_new_{user_id}")])
        keyboard.append([InlineKeyboardButton("📊 Сводный отчет", callback_data=f"report_daily_summary")])
        
        # Добавляем кнопку назад в зависимости от контекста
        if 'active_report_id' in context.user_data:
            keyboard.append([InlineKeyboardButton("⬅️ Назад к отчету", callback_data=f"report_show_{context.user_data['active_report_id']}")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if is_callback:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def show_daily_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать сводный отчет за день"""
        query = update.callback_query
        await query.answer()
        
        # Получаем сводный отчет
        summary = self.db.get_daily_report()
        
        message = "📈 СВОДНЫЙ ОТЧЕТ ЗА ДЕНЬ\n\n"
        message += f"📊 Количество смен: {summary['report_count']}\n"
        message += f"💵 Итог на утро: {summary['total_morning']} ₽\n"
        message += f"📝 Итог расходов: {summary['total_wasted']} ₽\n"
        message += f"💰 Итог прихода: {summary['total_in']} ₽\n"
        message += f"💳 Итог безнала: {summary['total_online']} ₽\n"
        message += f"📊 Итоговый остаток: {summary['total_rest']} ₽\n\n"
        
        # Рассчитываем общую выручку
        total_revenue = summary['total_in'] + summary['total_online']
        message += f"🏆 Общая выручка: {total_revenue} ₽\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"report_history_{update.effective_user.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback-запросов"""
        query = update.callback_query
        data = query.data
        
        try:
            if data == "main_menu":
                # Очищаем контекст отчетности
                keys_to_remove = ['active_report_id', 'creating_report', 'adding_expense', 
                                'expense_report_id', 'adding_cash_in', 'cash_in_report_id',
                                'adding_online', 'online_report_id']
                for key in keys_to_remove:
                    context.user_data.pop(key, None)
                
                # Возвращаем в главное меню
                from keyboards.global_keyb import get_main_keyboard
                await query.edit_message_text(
                    "Главное меню:",
                    reply_markup=await get_main_keyboard(user_id)
                )
                return
            elif data.startswith('report_show_'):
                report_id = int(data.split('_')[2])
                await self.show_report(update, context, report_id)
                
            elif data.startswith('report_add_expense_'):
                report_id = int(data.split('_')[3])
                await self.add_expense(update, context, report_id)
                
            elif data.startswith('report_add_cash_'):
                report_id = int(data.split('_')[3])
                await self.add_cash_in(update, context, report_id)
                
            elif data.startswith('report_add_online_'):
                report_id = int(data.split('_')[3])
                await self.add_online_cash(update, context, report_id)
                
            elif data.startswith('report_close_'):
                report_id = int(data.split('_')[2])
                await self.close_report(update, context, report_id)
                
            elif data.startswith('report_history_'):
                user_id = int(data.split('_')[2])
                await self.show_report_history(update, context, user_id)
                
            elif data.startswith('report_daily_summary'):
                await self.show_daily_summary(update, context)
                
            elif data.startswith('report_new_'):
                user_id = int(data.split('_')[2])
                # Создаем фейковый update для обработки
                fake_update = type('obj', (object,), {
                    'effective_user': type('obj', (object,), {'id': user_id}),
                    'message': query.message
                })()
                await self.start_new_report(fake_update, context)
            
            elif data.startswith('report_continue_'):
                report_id = int(data.split('_')[2])
                context.user_data['active_report_id'] = report_id
                await self.show_report(update, context, report_id)
                
            elif data.startswith('report_delete_'):
                report_id = int(data.split('_')[2])
                # Здесь можно добавить логику удаления отчета
                await query.answer("Функция удаления в разработке", show_alert=True)
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            try:
                await query.answer("❌ Произошла ошибка", show_alert=True)
            except:
                # Если не удалось ответить на callback, просто логируем
                logger.error(f"Не удалось ответить на callback: {e}")

    async def _show_report_message(self, update: Update, report_id: int, is_message: bool = False):
        """Вспомогательная функция для показа отчета (работает и с сообщениями и с callback)"""
        # Получаем данные отчета
        report = self.db.get_report_by_id(report_id)
        if not report:
            if is_message:
                await update.message.reply_text("❌ Отчет не найден")
            return
        
        # Получаем расходы
        expenses = self.db.get_report_expenses(report_id)
        
        # Формируем сообщение
        message = "📊 ОТЧЕТ О СМЕНЕ\n\n"
        message += f"ID: #{report['report_id']}\n"
        message += f"Дата: {report['created_at']}\n"
        message += f"Бариста: {report['username']}\n"
        message += f"Телефон: {report['phone_number']}\n"
        message += "─" * 30 + "\n"
        message += f"💵 Наличные на утро: {report['cash_morning']} ₽\n"
        
        if expenses:
            message += f"📝 Расходы ({len(expenses)}):\n"
            for expense in expenses:
                message += f"  • {expense['cash_rested']} ₽ - {expense['description']}\n"
        
        message += f"💰 Общий расход: {report['cash_wasted']} ₽\n"
        message += f"💸 Приход наличных: {report['cash_in']} ₽\n"
        message += f"💳 Безналичные: {report['cash_online']} ₽\n"
        message += "─" * 30 + "\n"
        message += f"📊 Остаток в кассе: {report['cash_rest']} ₽\n"
        
        if report['is_active']:
            message += f"🟢 Статус: Активная смена\n"
        else:
            message += f"🔴 Статус: Смена закрыта\n"
        
        if report['description']:
            message += f"📝 Примечание: {report['description']}\n"
        
        # Создаем клавиатуру
        keyboard = []
        if report['is_active']:
            keyboard.append([InlineKeyboardButton("➕ Добавить расход", callback_data=f"report_add_expense_{report_id}")])
            keyboard.append([InlineKeyboardButton("💰 Внести приход", callback_data=f"report_add_cash_{report_id}")])
            keyboard.append([InlineKeyboardButton("💳 Безналичные", callback_data=f"report_add_online_{report_id}")])
            keyboard.append([InlineKeyboardButton("✅ Закрыть смену", callback_data=f"report_close_{report_id}")])
        
        keyboard.append([InlineKeyboardButton("📋 История отчетов", callback_data=f"report_history_{update.effective_user.id}")])
        keyboard.append([InlineKeyboardButton("🗑️ Удалить отчет", callback_data=f"report_delete_{report_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if is_message:
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                # Для callback проверяем, изменилось ли сообщение
                try:
                    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
                except Exception as edit_error:
                    # Если сообщение не изменилось, просто отвечаем на callback
                    if "Message is not modified" in str(edit_error):
                        await update.callback_query.answer("✅ Данные обновлены")
                    else:
                        # Другие ошибки - логируем
                        logger.warning(f"Ошибка редактирования сообщения: {edit_error}")
                        await update.callback_query.answer("✅ Данные обновлены")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            if not is_message:
                await update.callback_query.answer("❌ Ошибка обновления", show_alert=True)

# Создаем глобальный экземпляр менеджера
report_manager = ReportWatchManager()