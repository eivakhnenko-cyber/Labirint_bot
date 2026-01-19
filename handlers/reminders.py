# handlers/reminders.py
import logging
from telegram import Update
from telegram.ext import CallbackContext
from datetime import time, datetime
import pytz
from config.buttons import Buttons
from keyboards.global_keyb import get_main_keyboard, get_back_keyboard 
from keyboards.remind_keyb import get_reminders_keyboard, get_reminder_type_keyboard, get_schedule_day_keyboard

logger = logging.getLogger(__name__)

try:
    from .reminder_manager import ReminderManager
 
    # Используем константы из класса
    DEFAULT_REMINDER_TIME = ReminderManager.DEFAULT_REMINDER_TIME
    DEFAULT_DAYS = ReminderManager.DEFAULT_DAYS
    MOSCOW_TZ = ReminderManager.LOCAL_TZ
    REMINDER_TYPES = ReminderManager.REMINDER_TYPES
except ImportError:
    # Фоллбэк на случай если класс еще не создан
    DEFAULT_REMINDER_TIME = time(10, 0)
    DEFAULT_DAYS = [1, 3]
    MOSCOW_TZ = pytz.timezone('Asia/Novosibirsk')
    REMINDER_TYPES = {
        "check_stock": "📦 Проверить остатки",
        "start_inventory": "🔄 Начать инвентаризацию",
        "custom": "➕ Свой вариант"
    }


async def manage_reminders(update: Update, context: CallbackContext) -> None:
    """Главное меню управления напоминаниями"""
    try:
        user_id = update.effective_user.id
        manager = ReminderManager()
        
        await clear_reminder_context(context, user_id)

        # Получаем статус через менеджер
        status_info = await manager.get_reminder_status(user_id)
        
        # Получаем полные настройки
        full_settings = await manager.get_full_reminder_settings(user_id)
        
        status_text = f"📅 Напоминания\n\n"
        status_text += f"Текущий статус: {status_info['status_text']}\n"
        
        if full_settings:
            # Форматируем дни
            day_names = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
            days = full_settings.get('days', manager.DEFAULT_DAYS)
            days_text = ", ".join([day_names.get(day, str(day)) for day in days])
            
            # Форматируем время
            reminder_time = full_settings.get('time', manager.DEFAULT_REMINDER_TIME)
            time_text = reminder_time.strftime("%H:%M") if isinstance(reminder_time, time) else "10:00"
            
            # Форматируем тип
            reminder_type = full_settings.get('type', 'check_stock')
            type_text = manager.REMINDER_TYPES.get(reminder_type, "📦 Проверить остатки")
            
            status_text += f"Тип: {type_text}\n"
            status_text += f"Дни: {days_text}\n"
            status_text += f"Время: {time_text}\n"
        
        status_text += "\nИспользуйте кнопки ниже для управления:"
        
        await update.message.reply_text(
            status_text,
            reply_markup=await get_reminders_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Ошибка в manage_reminders: {e}")
        await update.message.reply_text(
            "Ошибка загрузки настроек напоминаний.",
            reply_markup=await get_main_keyboard(user_id)
        )

async def setup_schedule(update: Update, context: CallbackContext) -> None:
    """Настройка расписания"""
    try:
        await update.message.reply_text(
            "📅 Выберите день недели для напоминаний:",
            reply_markup=get_schedule_day_keyboard()
        )
        context.user_data['awaiting_schedule_day'] = True
    except Exception as e:
        logger.error(f"Ошибка настройки расписания: {e}")
        await update.message.reply_text("Ошибка настройки расписания.")

async def start_reminders(update: Update, context: CallbackContext) -> None:
    """Включение напоминаний"""
    try:
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        manager = ReminderManager()

        # Проверяем доступность JobQueue
        if context.application.job_queue is None:
            await update.message.reply_text(
                "⚠️ JobQueue не доступен. Напоминания не могут быть включены.",
                reply_markup=await get_main_keyboard(user_id)
            )
            return

        # ✅ ИСПРАВЛЕНО: Используем save_reminder_settings, а не get_reminder_status
        success = await manager.save_reminder_settings(user_id, chat_id, True)
        
        if not success:
            await update.message.reply_text(
                "⚠️ Ошибка сохранения настроек.",
                reply_markup=await get_reminders_keyboard(user_id)
            )
            return
        
        # Создаем задания через менеджер
        success = await manager.setup_reminder_jobs(context, user_id, chat_id)
        
        if success:
            await update.message.reply_text(
                "🔔 Напоминания включены!\n\n"
                "Вы будете получать уведомления в соответствии с вашими настройками.\n"
                "Тестовое напоминание придет через 30 секунд.",
                reply_markup=await get_main_keyboard(user_id)
            )
        else:
            await update.message.reply_text(
                "⚠️ Ошибка создания заданий напоминаний.",
                reply_markup=await get_reminders_keyboard(user_id)
            )
        
    except Exception as e:
        logger.error(f"Ошибка включения напоминаний: {e}")
        await update.message.reply_text(
            "Ошибка включения напоминаний.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def stop_reminders(update: Update, context: CallbackContext) -> None:
    """Выключение напоминаний"""
    try:
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        manager = ReminderManager()  # ✅ СОЗДАЁМ ЛОКАЛЬНЫЙ МЕНЕДЖЕР
        
        # Сохраняем настройки через менеджер
        success = await manager.save_reminder_settings(user_id, chat_id, False)
        
        if success:
            # Удаляем задания через менеджер
            await manager._remove_reminder_jobs(context, user_id)
            
            await update.message.reply_text(
                "🔕 Напоминания выключены.\n\n"
                "Вы больше не будете получать уведомления об инвентаризации.",
                reply_markup=await get_main_keyboard(user_id)
            )
        else:
            await update.message.reply_text(
                "⚠️ Ошибка выключения напоминаний.",
                reply_markup=await get_reminders_keyboard(user_id)
            )
        
    except Exception as e:
        logger.error(f"Ошибка выключения напоминаний: {e}")
        await update.message.reply_text(
            "Ошибка выключения напоминаний.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def setup_reminder_type(update: Update, context: CallbackContext) -> None:
    """Настройка типа напоминания"""
    try:
        text = update.message.text
        user_id = update.effective_user.id
        manager = ReminderManager()
        
        logger.info(f"Обработка типа напоминания: текст='{text}', awaiting_reminder_type={context.user_data.get('awaiting_reminder_type', False)}")
         # Если флаг не установлен, но пришло сообщение - вероятно, пользователь не в том состоянии
        if not context.user_data.get('awaiting_reminder_type', False) and text not in [Buttons.BACK, Buttons.BACK_TO_MAIN]:
            logger.warning(f"Пользователь {user_id} отправил '{text}', но не в состоянии выбора типа напоминания")
            await manage_reminders(update, context)
            return
        
        if text == Buttons.BACK:
            await manage_reminders(update, context)
            return
        # ✅ ДОБАВЛЕНО: Проверяем, есть ли уже расписание
        settings = await manager.get_full_reminder_settings(user_id)
        has_schedule = settings and 'days' in settings and 'time' in settings
        
        message = "📝 Выберите тип напоминания:\n\n"
        message += "• 📦 Проверить остатки - стандартное напоминание\n"
        message += "• 🔄 Начать инвентаризацию - напоминание о начале полной инвентаризации\n"
        message += "• ➕ Свой вариант - введите свой текст напоминания\n\n"
        
        if not has_schedule:
            message += "⚠️ Внимание: расписание еще не настроено! После выбора типа нужно будет настроить дни и время."

        await update.message.reply_text(
            message,
            reply_markup=await get_reminder_type_keyboard()
        )
        context.user_data['awaiting_reminder_type'] = True
        
    except Exception as e:
        logger.error(f"Ошибка настройки типа напоминания: {e}")
        await update.message.reply_text(
            "Ошибка настройки типа напоминания.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def check_jobs(update: Update, context: CallbackContext) -> None:
    """Проверка активных заданий"""
    try:
        user_id = update.effective_user.id
        
        if not context.application.job_queue:
            await update.message.reply_text("⚠️ JobQueue не доступен.")
            return
        
        jobs = context.application.job_queue.jobs()
        user_jobs = [job for job in jobs if job.name and f"reminder_{user_id}_" in job.name]
        
        if user_jobs:
            message = f"📋 Активные задания ({len(user_jobs)}):\n\n"
            for job in user_jobs:
                next_run = job.next_t if hasattr(job, 'next_t') else None
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M") if next_run else "неизвестно"
                message += f"• {job.name}: {next_run_str}\n"
        else:
            message = "❌ Нет активных заданий"
        
        await update.message.reply_text(message, reply_markup=await get_main_keyboard(user_id))
        
    except Exception as e:
        logger.error(f"Ошибка проверки заданий: {e}")
        await update.message.reply_text("Ошибка проверки заданий.")

async def handle_reminder_type_selection(update: Update, context: CallbackContext) -> None:
    """Обработка выбора типа напоминания"""
    try:
        text = update.message.text
        user_id = update.effective_user.id
        manager = ReminderManager()

        if text == Buttons.BACK:
            await manage_reminders(update, context)
            return
        
        if text in ["📦 Проверить остатки", "🔄 Начать инвентаризацию"]:
            # Сохраняем тип напоминания
            reminder_type = "check_stock" if text == "📦 Проверить остатки" else "start_inventory"
            success = await manager.save_reminder_type(user_id, reminder_type)
            
            # ✅ ИСПРАВЛЕНО: Не переходим автоматически к выбору дня
            if success:
                await update.message.reply_text(
                    f"✅ Тип напоминания установлен: {text}",
                    reply_markup=await get_reminders_keyboard(user_id)
                )
            else:
                await update.message.reply_text(
                    f"❌ Ошибка сохранения типа напоминания",
                    reply_markup=await get_reminders_keyboard(user_id)
                )
            
        elif text == Buttons.OWN_VERSION:
            await update.message.reply_text(
                "Введите ваш вариант текста напоминания (максимум 100 символов):",
                reply_markup=get_back_keyboard()
            )
            context.user_data['awaiting_custom_reminder'] = True
            return
            
        else:
            await update.message.reply_text(
                "Выберите вариант из предложенных:",
                reply_markup=await get_reminder_type_keyboard()
            )
            return
            
        # ✅ ИСПРАВЛЕНО: Всегда сбрасываем флаги
        context.user_data.pop('awaiting_reminder_type', None)
        context.user_data.pop('return_to_schedule', None)
        
    except Exception as e:
        logger.error(f"Ошибка обработки типа напоминания: {e}")
        await update.message.reply_text(
            "Ошибка сохранения типа напоминания.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def handle_custom_reminder_input(update: Update, context: CallbackContext) -> None:
    """Обработка ввода custom напоминания"""
    try:
        custom_text = update.message.text.strip()
        user_id = update.effective_user.id
        manager = ReminderManager()

        if custom_text == Buttons.BACK_TO_MAIN:
            await setup_reminder_type(update, context)
            return
        
        if custom_text and len(custom_text) <= 100:
            await manager.save_custom_reminder(user_id, custom_text)
            
            # ✅ ИСПРАВЛЕНО: Убрали автоматический переход к выбору дня
            await update.message.reply_text(
                f"✅ Ваш текст напоминания сохранен:\n\"{custom_text}\"",
                reply_markup=await get_reminders_keyboard(user_id)
            )
        else:
            await update.message.reply_text(
                "Текст должен быть от 1 до 100 символов. Попробуйте снова:",
                reply_markup=get_back_keyboard()
            )
            return
            
        # ✅ ИСПРАВЛЕНО: Сбрасываем все флаги
        context.user_data.pop('awaiting_custom_reminder', None)
        context.user_data.pop('awaiting_reminder_type', None)
        context.user_data.pop('return_to_schedule', None)
        
    except Exception as e:
        logger.error(f"Ошибка обработки custom напоминания: {e}")
        await update.message.reply_text(
            "Ошибка сохранения текста напоминания.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def handle_schedule_day_selection(update: Update, context: CallbackContext) -> None:
    """Обработка выбора дня для напоминаний"""
    try:
        text = update.message.text.strip()
        user_id = update.effective_user.id
        manager = ReminderManager()

        logger.info(f"Обработка выбора дня: {text}")
        
        if text == Buttons.BACK:
            await manage_reminders(update, context)
            # Сбрасываем флаг
            context.user_data.pop('awaiting_schedule_day', None)
            return
           
        # Парсим выбранный день
        day_map = {
            "Пн": 0, "Вт": 1, "Ср": 2, 
            "Чт": 3, "Пт": 4, "Сб": 5, "Вс": 6
        }
        
        # Разделяем текст на части
        parts = text.split()
        day_part = parts[0]  # Первая часть - день
        
        # Если есть вторая часть, это может быть время
        if len(parts) > 1 and ":" in parts[1]:
            time_part = parts[1]
            
            try:
                reminder_time = datetime.strptime(time_part, "%H:%M").time()
                selected_day = day_map.get(day_part)
                
                if selected_day is not None:
                    # Сохраняем день и время
                    success_days = await manager.save_reminder_days(user_id, [selected_day])
                    success_time = await manager.save_reminder_time(user_id, reminder_time)
                    
                    if success_days and success_time:
                        day_names = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
                        day_name = day_names.get(selected_day, str(selected_day))
                        
                        await update.message.reply_text(
                            f"✅ Расписание обновлено!\n\n"
                            f"Напоминания будут приходить по {day_name} в {time_part}.",
                            reply_markup=await get_reminders_keyboard(user_id)
                        )
                        
                        # Сбрасываем флаги
                        context.user_data.pop('awaiting_schedule_day', None)
                        context.user_data.pop('awaiting_schedule_time', None)
                        context.user_data.pop('selected_day', None)
                        return
                    
            except ValueError:
                pass
        
        # Если это просто выбор дня без времени
        selected_day = day_map.get(day_part)
        
        if selected_day is not None:
            # Сохраняем выбранный день
            context.user_data['selected_day'] = selected_day
            context.user_data['awaiting_schedule_time'] = True
            context.user_data.pop('awaiting_schedule_day', None)
            
            day_names_full = {0: "Понедельник", 1: "Вторник", 2: "Среда", 
                              3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
            
            await update.message.reply_text(
                f"✅ Выбран день: {day_names_full.get(selected_day, text)}\n\n"
                f"Теперь введите время для напоминаний в формате ЧЧ:ММ (например, 09:30 или 14:00):\n\n"
                f"Или нажмите '🔙 Назад' чтобы выбрать другой день.",
                reply_markup=get_back_keyboard()
            )
        else:
            # Если текст не день и не время - это может быть время, которое мы пропустили
            # ✅ ПРОСТАЯ ПРОВЕРКА: если это время, просим сначала выбрать день
            try:
                # Проверяем формат времени
                datetime.strptime(text, "%H:%M").time()
                # Это время, но день не выбран
                await update.message.reply_text(
                    "Сначала выберите день недели из списка:",
                    reply_markup=get_schedule_day_keyboard()
                )
                return
            except ValueError:
                # Не день и не время
                await update.message.reply_text(
                    f"Не удалось распознать день '{text}'. Пожалуйста, выберите день из списка:",
                    reply_markup=get_schedule_day_keyboard()
                )
            
    except Exception as e:
        logger.error(f"Ошибка обработки расписания: {e}", exc_info=True)
        await update.message.reply_text(
            "Ошибка сохранения расписания.",
            reply_markup=await get_reminders_keyboard(user_id)
        )
        context.user_data.pop('awaiting_schedule_day', None)
        context.user_data.pop('awaiting_schedule_time', None)

async def handle_time_input(update: Update, context: CallbackContext) -> None:
    """Обработка ввода времени"""
    try:
        time_text = update.message.text.strip()
        user_id = update.effective_user.id
        selected_day = context.user_data.get('selected_day')
        manager = ReminderManager()

        # ✅ ПРОВЕРКА: Если пользователь НЕ в состоянии ввода времени
        if not context.user_data.get('awaiting_schedule_time'):
            # Это может быть кнопка "Назад" или другой ввод
            if time_text == Buttons.BACK:
                await manage_reminders(update, context)
                return
            else:
                # Перенаправляем в выбор дня
                await handle_schedule_day_selection(update, context)
                return

        # Проверяем, не нажата ли кнопка "Назад"
        if time_text == Buttons.BACK:
            # Возвращаемся к выбору дня
            await update.message.reply_text(
                "Выберите день недели для напоминаний:",
                reply_markup=get_schedule_day_keyboard()
            )
            
            # Меняем флаги
            context.user_data['awaiting_schedule_day'] = True
            context.user_data.pop('awaiting_schedule_time', None)
            context.user_data.pop('selected_day', None)
            return
        
        # Проверяем формат времени
        try:
            reminder_time = datetime.strptime(time_text, "%H:%M").time()
            selected_day = context.user_data.get('selected_day')
            
            if selected_day is None:
                await update.message.reply_text(
                    "Ошибка: день не выбран. Начните с начала.",
                    reply_markup=await get_reminders_keyboard(user_id)
                )
                return
            
            # Сохраняем день и время
            success_days = await manager.save_reminder_days(user_id, [selected_day])
            success_time = await manager.save_reminder_time(user_id, reminder_time)
            
            if success_days and success_time:
                day_names = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
                day_name = day_names.get(selected_day, str(selected_day))
                
                # Получаем текущий тип напоминания
                current_type = await manager._get_reminder_type_db(user_id)
                
                # ✅ ИСПРАВЛЕНО: УБИРАЕМ ЛИШНЕЕ СООБЩЕНИЕ - проверяем, есть ли тип
                if not current_type or current_type == 'check_stock':
                    # Если тип не установлен - предлагаем выбрать
                    await update.message.reply_text(
                        f"✅ Расписание обновлено!\n\n"
                        f"Напоминания будут приходить по {day_name} в {time_text}.\n\n"
                        f"Теперь выберите тип напоминания:",
                        reply_markup=await get_reminder_type_keyboard()
                    )
                    context.user_data['awaiting_reminder_type'] = True
                else:
                    # Если тип уже установлен - просто подтверждаем сохранение расписания
                    await update.message.reply_text(
                        f"✅ Расписание обновлено!\n\n"
                        f"Напоминания будут приходить по {day_name} в {time_text}.",
                        reply_markup=await get_reminders_keyboard(user_id)
                    )
            else:
                await update.message.reply_text(
                    "❌ Ошибка сохранения расписания.",
                    reply_markup=await get_reminders_keyboard(user_id)
                )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени.\n\n"
                "Введите время в формате ЧЧ:ММ (например, 09:30 или 14:00):\n\n"
                "Или нажмите '🔙 Назад' чтобы выбрать другой день.",
                reply_markup=get_back_keyboard()
            )
            return
            
        # Сбрасываем флаги при успешном сохранении
        context.user_data.pop('awaiting_schedule_time', None)
        context.user_data.pop('selected_day', None)
        context.user_data.pop('awaiting_schedule_day', None)
        
    except Exception as e:
        logger.error(f"Ошибка обработки времени: {e}")
        await update.message.reply_text(
            "Ошибка сохранения времени.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def send_reminder(update: Update, context: CallbackContext) -> None:
    """Отправка напоминания пользователю с учетом типа"""
    try:
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        manager = ReminderManager()

        success = await manager.send_reminder_callback(user_id)

        logger.info(f"send_reminder вызвана! Тип context: {type(context)}")

        # Для Job контекста получаем данные из job.data
        if not success:
            await update.message.reply_text(user_id)
            return
            
        logger.info(f"Отправка напоминания пользователю {user_id}, чат {chat_id}")

        # Получаем тип напоминания
        reminder_type = await manager._get_reminder_type_db(user_id)
        logger.info(f"Тип напоминания: {reminder_type}")

        # Формируем сообщение в зависимости от типа
        if reminder_type == 'check_stock':
            # Стандартное напоминание о проверке остатков
            inventory_list = await manager.get_user_inventory(user_id)
            
            if inventory_list:
                message_text = (
                    "⏰ НАПОМИНАНИЕ: ПРОВЕРИТЬ ОСТАТКИ\n\n"
                    "Пора проверить наличие товаров:\n"
                    f"{inventory_list}\n\n"
                    "Используйте кнопку '✅ Подтвердить инвентаризацию' "
                    "после завершения проверки."
                )
            else:
                message_text = (
                    "⏰ НАПОМИНАНИЕ: ПРОВЕРИТЬ ОСТАТКИ\n\n"
                    "Пора провести проверку остатков!\n\n"
                    "Ваш список товаров пуст. "
                    "Добавьте товары через меню '➕ Добавить товар'."
                )
                
        elif reminder_type == 'start_inventory':
            # Напоминание о начале полной инвентаризации
            message_text = (
                "🔄 НАПОМИНАНИЕ: НАЧАТЬ ИНВЕНТАРИЗАЦИЮ\n\n"
                "Пора начать полную инвентаризацию!\n\n"
                "Перейдите в меню инвентаризации для начала процесса."
            )
            
        elif reminder_type == 'custom':
            # Пользовательский текст напоминания
            custom_text = await manager._get_custom_reminder_text(user_id)
            if custom_text:
                message_text = f"⏰ НАПОМИНАНИЕ:\n\n{custom_text}"
            else:
                message_text = "⏰ НАПОМИНАНИЕ: Пора провести инвентаризацию!"
        else:
            # Напоминание по умолчанию
            message_text = "⏰ НАПОМИНАНИЕ: Пора проверить остатки товаров!"
        
        logger.info(f"Отправляю сообщение: {message_text[:50]}...")

        await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=await get_main_keyboard(user_id)
        )
        
        # Логируем отправку напоминания
        logger.info(f"✅ Отправлено напоминание пользователю {user_id}, тип: {reminder_type}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")

async def show_reminders_status(update: Update, context: CallbackContext) -> None:
    """Показывает текущий статус напоминаний"""
    try:
        manager = ReminderManager()
        user_id = update.effective_user.id
        status = await manager.get_reminder_status(user_id)
        settings = await manager.get_full_reminder_settings(user_id)
        
        status_text = "✅ Включены" if status else "❌ Выключены"
        
        message = f"📊 Статус напоминаний:\n\n"
        message += f"Состояние: {status_text}\n"
        
        if settings:
            # Форматируем дни
            day_names = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
            days = settings.get('days', DEFAULT_DAYS)
            days_text = ", ".join([day_names.get(day, str(day)) for day in days])
            
            # Форматируем время
            reminder_time = settings.get('time', DEFAULT_REMINDER_TIME)
            time_text = reminder_time.strftime("%H:%M") if isinstance(reminder_time, time) else "10:00"
            
            # Форматируем тип
            reminder_type = settings.get('type', 'check_stock')

            if reminder_type == 'custom':
                custom_text = await manager.get_custom_reminder_text(user_id)
                if custom_text:
                    # Обрезаем длинный текст для отображения
                    display_text = custom_text[:50] + "..." if len(custom_text) > 50 else custom_text
                    type_text = f"➕ Свой вариант: \"{display_text}\""
                else:
                    type_text = "➕ Свой вариант (текст не задан)"
            else:

                type_text = REMINDER_TYPES.get(reminder_type, "📦 Проверить остатки")
            
            message += f"Тип: {type_text}\n"
            message += f"Дни: {days_text}\n"
            message += f"Время: {time_text}\n"

            # Добавляем информацию о custom тексте если он есть
            if reminder_type == 'custom' and 'custom_text' in settings:
                full_custom_text = settings.get('custom_text', '')
                if full_custom_text and len(full_custom_text) > 50:
                    message += f"\n📝 Полный текст: \"{full_custom_text}\"\n"
        
        await update.message.reply_text(
            message,
            reply_markup=await get_reminders_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа статуса напоминаний: {e}")
        await update.message.reply_text(
            "Ошибка загрузки статуса напоминаний.",
            reply_markup=await get_reminders_keyboard(user_id)
        )

async def clear_reminder_context(context: CallbackContext, user_id: int) -> None:
    """Очищает контекст напоминаний для пользователя"""
    try:
        # Удаляем все флаги ожидания
        keys_to_remove = []
        for key in list(context.user_data.keys()):
            if key.startswith('awaiting_') or key in ['selected_day', 'selected_time']:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            context.user_data.pop(key, None)
            
    except Exception as e:
        logger.error(f"Ошибка очистки контекста: {e}")

async def reload_reminders(update: Update, context: CallbackContext) -> None:
    """Перезагружает задания напоминаний"""
    try:
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        manager = ReminderManager()

        # Проверяем статус
        status = await manager.get_reminder_status(user_id)
       
        if not status:
            await update.message.reply_text(
                "Напоминания выключены. Включите их сначала.",
                reply_markup=await get_reminders_keyboard(user_id)
            )
            return
        
        # Удаляем старые задания
        await manager._remove_reminder_jobs(context, user_id)
        
        # Создаем новые задания
        await manager.setup_reminder_jobs(context, user_id, chat_id)
        
        await update.message.reply_text(
            "✅ Задания напоминаний перезагружены!",
            reply_markup=await get_main_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка перезагрузки напоминаний: {e}")
        await update.message.reply_text("Ошибка перезагрузки напоминаний.")