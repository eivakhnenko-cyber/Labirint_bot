import logging
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, filters, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler

from keyboards.bonus_keyb import *

from rep_bonus.bonus_levels_class import bonus_levels_manager
from handlers.admin_roles_class import role_manager, Permission, UserRole
from rep_bonus.bonus_levels_delete import delete_level_inline_handler


logger = logging.getLogger(__name__)


# Состояния для ConversationHandler
SELECT_PROGRAM, LEVEL_NAME, MIN_PURCHASES, BONUS_PERCENT, DESCRIPTION, CONFIRM = range(6)

async def create_level_handler(update: Update, context: CallbackContext) -> int:
    """
    НАЧАЛО СОЗДАНИЯ УРОВНЯ (entry point для ConversationHandler)
    Привязывается к кнопке "Создать уровень".
    Начинает процесс создания уровня через ConversationHandler.
    """
    user_id = update.effective_user.id
    
    # Проверка прав
    if not await role_manager.has_permission(user_id, Permission.MANAGE_BONUSES):
        await update.message.reply_text(
            "⛔ У вас нет прав для создания уровней.",
            reply_markup=await get_bonus_system_keyboard()
        )
        return ConversationHandler.END
    
    # Получаем активные программы
    programs = bonus_levels_manager.get_active_bonus_programs()
    
    if not programs:
        await update.message.reply_text(
            "📭 Нет активных бонусных программ.\n"
            "Сначала создайте программу лояльности.",
            reply_markup=await get_bonus_system_keyboard(user_id)
        )
        return ConversationHandler.END
    
    # Формируем список программ для выбора
    programs_text = "📋 *Выберите программу:*\n\n"
    for i, program in enumerate(programs, 1):
        programs_text += f"{i}. {program[1]}\n"
    
    programs_text += "\nОтправьте номер программы или название"
    
    # Сохраняем список программ в context
    context.user_data['programs_list'] = programs
    
    await update.message.reply_text(
        programs_text,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    return SELECT_PROGRAM

async def select_program_handler(update: Update, context: CallbackContext) -> int:
    """
    ОБРАБОТКА ВЫБОРА ПРОГРАММЫ (состояние SELECT_PROGRAM)
    Обрабатывает выбор программы для создания уровня.
    """
    user_input = update.message.text.strip()
    programs = context.user_data.get('programs_list', [])
    
    selected_program = None

    # Проверяем ввод номера
    if user_input.isdigit():
        index = int(user_input) - 1
        if 0 <= index < len(programs):
            selected_program = programs[index]
    
    # Проверяем ввод названия
    if not selected_program:
        for program in programs:
            if user_input.lower() in program[1].lower():
                selected_program = program
                break
    
    if not selected_program:
        await update.message.reply_text(
            "❌ Программа не найдена. Пожалуйста, выберите номер или название из списка:"
        )
        return SELECT_PROGRAM
    
    # Сохраняем выбранную программу
    context.user_data['selected_program'] = {
        'id': selected_program[0],
        'name': selected_program[1]
    }

    await update.message.reply_text(
        f"✅ Выбрана программа: *{selected_program[1]}*\n\n"
        f"📝 Введите название уровня (например: 'Бронзовый', 'Серебряный', 'Золотой'):",
        parse_mode='Markdown'
    )
    
    return LEVEL_NAME

async def level_name_handler(update: Update, context: CallbackContext) -> int:
    """
    ОБРАБОТКА ВВОДА НАЗВАНИЯ УРОВНЯ (состояние LEVEL_NAME)
    Обрабатывает ввод названия уровня.
    """
    level_name = update.message.text.strip()
    
    if len(level_name) < 2 or len(level_name) > 50:
        await update.message.reply_text(
            "❌ Название уровня должно быть от 2 до 50 символов.\n"
            "Пожалуйста, введите название уровня:"
        )
        return LEVEL_NAME
    
    context.user_data['level_name'] = level_name
    
    await update.message.reply_text(
        f"✅ Название уровня: *{level_name}*\n\n"
        f"💰 Введите минимальную сумму покупок для достижения уровня (в рублях):\n"
        f"_Пример: 1000 или 1500.50_",
        parse_mode='Markdown'
    )
    
    return MIN_PURCHASES

async def min_purchases_handler(update: Update, context: CallbackContext) -> int:
    """
    ОБРАБОТКА ВВОДА МИНИМАЛЬНОЙ СУММЫ (состояние MIN_PURCHASES)
    Обрабатывает ввод минимальной суммы покупок для уровня.
    """
    try:
        min_purchases = float(update.message.text.strip().replace(',', '.'))
        
        if min_purchases <= 0:
            await update.message.reply_text(
                "❌ Сумма должна быть больше 0.\n"
                "Пожалуйста, введите минимальную сумму покупок:"
            )
            return MIN_PURCHASES
        
        context.user_data['min_purchases'] = min_purchases
        
        await update.message.reply_text(
            f"✅ Минимальная сумма: *{min_purchases} руб.*\n\n"
            f"📈 Введите процент бонусов для этого уровня (например: 5, 10, 15):\n"
            f"_Максимально 100%_",
            parse_mode='Markdown'
        )
        
        return BONUS_PERCENT
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное число.\n"
            "Введите минимальную сумму покупок:"
        )
        return MIN_PURCHASES

async def bonus_percent_handler(update: Update, context: CallbackContext) -> int:
    """
    ОБРАБОТКА ВВОДА ПРОЦЕНТА БОНУСОВ (состояние BONUS_PERCENT)
    Обрабатывает ввод процента бонусов для уровня.
    """
    try:
        bonus_percent = float(update.message.text.strip().replace(',', '.'))
        
        if bonus_percent < 0 or bonus_percent > 100:
            await update.message.reply_text(
                "❌ Процент должен быть от 0 до 100.\n"
                "Пожалуйста, введите процент бонусов:"
            )
            return BONUS_PERCENT
        
        context.user_data['bonus_percent'] = bonus_percent
        
        await update.message.reply_text(
            f"✅ Процент бонусов: *{bonus_percent}%*\n\n"
            f"📝 Введите описание уровня (необязательно):\n"
            f"_Нажмите /skip чтобы пропустить_",
            parse_mode='Markdown'
        )
        
        return DESCRIPTION
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное число.\n"
            "Введите процент бонусов:"
        )
        return BONUS_PERCENT

async def description_handler(update: Update, context: CallbackContext) -> int:
    """
    ОБРАБОТКА ВВОДА ОПИСАНИЯ (состояние DESCRIPTION)
    Обрабатывает ввод описания уровня или пропуск этого шага.
    """
    if update.message.text != '/skip':
        description = update.message.text.strip()
        if len(description) > 500:
            await update.message.reply_text(
                "❌ Описание слишком длинное (максимум 500 символов).\n"
                "Пожалуйста, введите описание:"
            )
            return DESCRIPTION
        context.user_data['description'] = description
    else:
        context.user_data['description'] = None
    
    # Формируем подтверждение
    program = context.user_data['selected_program']
    
    confirmation_text = (
        f"📋 *Подтвердите создание уровня:*\n\n"
        f"🏷️ *Программа:* {program['name']}\n"
        f"📊 *Уровень:* {context.user_data['level_name']}\n"
        f"💰 *Мин. сумма:* {context.user_data['min_purchases']} руб.\n"
        f"📈 *Бонус:* {context.user_data['bonus_percent']}%\n"
    )
    
    if context.user_data.get('description'):
        confirmation_text += f"📝 *Описание:* {context.user_data['description']}\n"
    
    confirmation_text += "\n✅ Создать уровень?"
    
    await update.message.reply_text(
        confirmation_text,
        parse_mode='Markdown',
        reply_markup=get_confirm_bonus_keyboard()
    )
    
    return CONFIRM

async def confirm_create_level_handler(update: Update, context: CallbackContext) -> int:
    """
    ПОДТВЕРЖДЕНИЕ СОЗДАНИЯ УРОВНЯ (состояние CONFIRM)
    Обрабатывает финальное подтверждение создания уровня.
    """
    user_choice = update.message.text.strip()
    
    if user_choice == Buttons.CONFIRM_YES:
        # Создаем уровень
        program = context.user_data['selected_program']
        level_id = bonus_levels_manager.create_bonus_level(
            program_id=program['id'],
            level_name=context.user_data['level_name'],
            min_total_purchases=context.user_data['min_purchases'],
            bonus_percent=context.user_data['bonus_percent'],
            description=context.user_data.get('description')
        )
        
        if level_id:
            await update.message.reply_text(
                f"✅ Уровень *{context.user_data['level_name']}* успешно создан!\n"
                f"ID уровня: {level_id}",
                parse_mode='Markdown',
                reply_markup=await get_levels_management_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при создании уровня. Попробуйте позже.",
                reply_markup=await get_levels_management_keyboard()
            )
    else:
        await update.message.reply_text(
            "❌ Создание уровня отменено.",
            reply_markup=await get_levels_management_keyboard()
        )
    
    # Очищаем данные
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel_create_level_handler(update: Update, context: CallbackContext) -> int:
    """
    ОТМЕНА СОЗДАНИЯ УРОВНЯ (fallback для ConversationHandler)
    Обрабатывает отмену процесса создания уровня.
    """
    await update.message.reply_text(
        "❌ Создание уровня отменено.",
        reply_markup=await get_levels_management_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def list_levels_handler(update: Update, context: CallbackContext) -> None:
    """
    СПИСОК УРОВНЕЙ БОНУСНЫХ ПРОГРАММ
    Привязывается к кнопке "Список уровней".
    Показывает все уровни всех бонусных программ.
    """
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.VIEW_BONUSES):
        await update.message.reply_text(
            "⛔ У вас нет прав для просмотра уровней.",
            reply_markup=await get_bonus_system_keyboard()
        )
        return
    
    # Получаем все уровни
    levels = bonus_levels_manager.get_bonus_levels(user_id)
    
    if not levels:
        await update.message.reply_text(
            "📭 Уровни бонусных программ еще не созданы.",
            reply_markup=await get_levels_management_keyboard()
        )
        return
    
    # Группируем уровни по программам
    programs_levels = {}
    for level in levels:
        program_name = level[6]  # program_name из join
        if program_name not in programs_levels:
            programs_levels[program_name] = []
        programs_levels[program_name].append(level)
    
    # Формируем сообщение
    message_text = "📋 *Список уровней бонусных программ:*\n\n"
    
    for program_name, levels_list in programs_levels.items():
        message_text += f"🏷️ *{program_name}:*\n"
        
        for level in levels_list:
            level_id = level[0]
            level_name = level[2]
            min_purchases = level[3]
            bonus_percent = level[4]
            description = level[5] if level[5] else "нет описания"
            
            message_text += (
                f"  └─ *{level_name}* (ID: {level_id})\n"
                f"     💰 От {min_purchases} руб. | 🎁 {bonus_percent}%\n"
                f"     📝 {description}\n\n"
            )
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=await get_levels_management_keyboard()
    )

async def edit_level_handler(update: Update, context: CallbackContext) -> None:
    """Редактирование уровня"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_BONUSES):
        await update.message.reply_text(
            "⛔ У вас нет прав для редактирования уровней.",
            reply_markup=await get_bonus_system_keyboard()
        )
        return
    
    # Проверяем, есть ли аргументы
    if not context.args:
        await update.message.reply_text(
            "✏️ *Редактирование уровня*\n\n"
            "Использование:\n"
            "/editlevel <ID_уровня> [параметры]\n\n"
            "Параметры (необязательно):\n"
            "-name <новое_название>\n"
            "-min <минимальная_сумма>\n"
            "-bonus <процент_бонусов>\n"
            "-desc <описание>\n\n"
            "Примеры:\n"
            "/editlevel 1 -name \"Золотой VIP\"\n"
            "/editlevel 2 -bonus 15 -desc \"Высокий уровень\"",
            #parse_mode='Markdown',
            reply_markup=await get_levels_management_keyboard()
        )
        return
    
    try:
        level_id = int(context.args[0])
        
        # Получаем текущий уровень
        level = bonus_levels_manager.get_bonus_level(level_id)
        
        if not level:
            await update.message.reply_text(
                "❌ Уровень не найден.",
                reply_markup=await get_levels_management_keyboard()
            )
            return
        
        # Парсим аргументы
        update_data = {}
        args = context.args[1:]
        
        i = 0
        while i < len(args):
            if args[i] == '-name' and i + 1 < len(args):
                update_data['level_name'] = args[i + 1]
                i += 2
            elif args[i] == '-min' and i + 1 < len(args):
                try:
                    update_data['min_total_purchases'] = float(args[i + 1])
                    i += 2
                except ValueError:
                    await update.message.reply_text(
                        "❌ Неверный формат суммы.",
                        reply_markup=await get_levels_management_keyboard()
                    )
                    return
            elif args[i] == '-bonus' and i + 1 < len(args):
                try:
                    update_data['bonus_percent'] = float(args[i + 1])
                    i += 2
                except ValueError:
                    await update.message.reply_text(
                        "❌ Неверный формат процента.",
                        reply_markup=await get_levels_management_keyboard()
                    )
                    return
            elif args[i] == '-desc' and i + 1 < len(args):
                update_data['description'] = args[i + 1]
                i += 2
            else:
                i += 1
        
        if not update_data:
            await update.message.reply_text(
                "❌ Не указаны параметры для изменения.",
                reply_markup=await get_levels_management_keyboard()
            )
            return
        
        # Обновляем уровень
        if bonus_levels_manager.update_bonus_level(level_id, **update_data):
            await update.message.reply_text(
                f"✅ Уровень *{level[2]}* успешно обновлен!\n\n"
                f"Измененные параметры:\n" +
                "\n".join([f"• {k}: {v}" for k, v in update_data.items()]),
                parse_mode='Markdown',
                reply_markup=await get_levels_management_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при обновлении уровня.",
                reply_markup=await get_levels_management_keyboard()
            )
            
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат ID уровня.",
            reply_markup=await get_levels_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования уровня: {e}")
        await update.message.reply_text(
            "❌ Ошибка при редактировании уровня.",
            reply_markup=await get_levels_management_keyboard()
        )

async def level_statistics_handler(update: Update, context: CallbackContext) -> None:
    """
    СТАТИСТИКА УРОВНЕЙ
    Привязывается к кнопке "Статистика уровней".
    Показывает статистику по уровням (в разработке).
    """
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.VIEW_BONUSES):
        await update.message.reply_text(
            "⛔ У вас нет прав для просмотра статистики.",
            reply_markup=await get_bonus_system_keyboard()
        )
        return
    
    # Здесь можно добавить логику для сбора статистики
    # Например, количество пользователей на каждом уровне
    
    await update.message.reply_text(
        "📊 *Статистика уровней*\n\n"
        "📈 *Функция в разработке*\n\n"
        "В будущем здесь будет отображаться:\n"
        "• Количество пользователей на каждом уровне\n"
        "• Средняя сумма покупок\n"
        "• Распределение по уровням\n"
        "• Динамика переходов между уровнями",
        parse_mode='Markdown',
        reply_markup=await get_levels_management_keyboard()
    )

async def delete_level_handler(update: Update, context: CallbackContext) -> None:
    """
    УДАЛЕНИЕ УРОВНЯ
    """
    await delete_level_inline_handler(update, context)
    
async def confirm_delete_level_handler(update: Update, context: CallbackContext) -> None:
    """
    ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ УРОВНЯ
    Обрабатывает ответ пользователя после запроса подтверждения удаления.
    """
    user_choice = update.message.text.strip()
    level_id = context.user_data.get('level_to_delete')
    
    if not level_id:
        await update.message.reply_text(
            "❌ Данные для удаления устарели. Начните заново.",
            reply_markup=await get_levels_management_keyboard()
        )
        # Очищаем контекст
        context.user_data.pop('level_to_delete', None)
        context.user_data.pop('awaiting_delete_confirmation', None)
        return
    
    if user_choice == Buttons.CONFIRM_DEL_YES:
        # Получаем информацию об уровне перед удалением
        level = bonus_levels_manager.get_bonus_level(level_id)
        level_name = level[2] if level else "неизвестный уровень"
        
        if bonus_levels_manager.delete_bonus_level(level_id):
            await update.message.reply_text(
                f"✅ Уровень '{level_name}' успешно удален!",
                reply_markup=await get_levels_management_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при удалении уровня.",
                reply_markup=await get_levels_management_keyboard()
            )
    else:
        await update.message.reply_text(
            "❌ Удаление отменено.",
            reply_markup=await get_levels_management_keyboard()
        )
    
    # Очищаем контекст в любом случае
    context.user_data.pop('level_to_delete', None)
    context.user_data.pop('awaiting_delete_confirmation', None)

# Conversation Handler для создания уровня
create_level_conversation = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(Buttons.ADD_LEVELS), create_level_handler)],
    states={
        SELECT_PROGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_program_handler)],
        LEVEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, level_name_handler)],
        MIN_PURCHASES: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_purchases_handler)],
        BONUS_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_percent_handler)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler),
                     CommandHandler('skip', description_handler)],
        CONFIRM: [MessageHandler(filters.Text([Buttons.CONFIRM_YES, Buttons.CONFIRM_NO]), confirm_create_level_handler)]
    },
    fallbacks=[CommandHandler('cancel', cancel_create_level_handler)],
    allow_reentry=True
)