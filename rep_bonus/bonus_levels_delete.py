import logging
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, filters, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler

from keyboards.bonus_keyb import *

from rep_bonus.bonus_levels_class import bonus_levels_manager
from handlers.admin_roles_class import role_manager, Permission, UserRole

logger = logging.getLogger(__name__)


# Добавьте после импортов или перед функциями
DELETE_LEVEL_CALLBACK_PREFIX = "delete_level_"
CONFIRM_DELETE_CALLBACK_PREFIX = "confirm_delete_"
CANCEL_DELETE_CALLBACK = "cancel_delete"

async def delete_level_inline_handler(update: Update, context: CallbackContext) -> None:
    """
    УДАЛЕНИЕ УРОВНЯ через inline-кнопки
    Показывает список уровней с inline-кнопками для выбора
    """
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_BONUSES):
        await update.message.reply_text(
            "⛔ У вас нет прав для удаления уровней.",
            reply_markup=await get_bonus_system_keyboard()
        )
        return
    
    # Получаем все уровни
    levels = bonus_levels_manager.get_bonus_levels()
    
    if not levels:
        await update.message.reply_text(
            "📭 Нет доступных уровней для удаления.",
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
    
    # ИНИЦИАЛИЗИРУЕМ переменную message_text
    message_text = "🗑️ *Выберите уровень для удаления:*\n\n"
    

    # Создаем inline-клавиатуру
    keyboard = []
    
    for program_name, levels_list in programs_levels.items():
        # Добавляем программу в текстовое сообщение
        message_text += f"🏷️ *{program_name}:*\n"
        
        # Добавляем кнопки для каждого уровня
        for level in levels_list:
            level_id = level[0]
            level_name = level[2]
            min_purchases = level[3]
            bonus_percent = level[4]
            
            # Добавляем в текстовое сообщение
            message_text += f"  - {level_name} (ID: {level_id})\n"

            # Текст на кнопке
            button_text = f"🗑️ {level_name} (от {min_purchases} руб. | {bonus_percent}%)"
            
            # Callback данные
            callback_data = f"{DELETE_LEVEL_CALLBACK_PREFIX}{level_id}"
            
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=callback_data)
            ])
            message_text += "\n"
    
    message_text += "\nНажмите на кнопку уровня, который хотите удалить:"
    
    # Добавляем кнопку отмены
    keyboard.append([
        InlineKeyboardButton("❌ Отмена", callback_data=CANCEL_DELETE_CALLBACK)
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🗑️ *Выберите уровень для удаления:*\n\n"
        "Нажмите на кнопку уровня, который хотите удалить:",
        #parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_delete_level_callback(update: Update, context: CallbackContext) -> None:
    """
    Обработка нажатия на inline-кнопку удаления уровня
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Отмена удаления
    if callback_data == CANCEL_DELETE_CALLBACK:
        await query.edit_message_text(
            "❌ Удаление отменено.",
            reply_markup=await get_levels_management_keyboard()
        )
        return
    
    # Обработка выбора уровня для удаления
    if callback_data.startswith(DELETE_LEVEL_CALLBACK_PREFIX):
        level_id = int(callback_data.replace(DELETE_LEVEL_CALLBACK_PREFIX, ""))
        
        # Получаем информацию об уровне
        level = bonus_levels_manager.get_bonus_level(level_id)
        if not level:
            await query.edit_message_text(
                "❌ Уровень не найден.",
                reply_markup=await get_levels_management_keyboard()
            )
            return
        
        # Сохраняем ID уровня в контекст
        context.user_data['level_to_delete_inline'] = level_id
        
        # Показываем подтверждение с inline-кнопками
        confirmation_text = (
            f"⚠️ *Подтвердите удаление уровня:*\n\n"
            f"🏷️ *Программа:* {level[6]}\n"
            f"📊 *Уровень:* {level[2]}\n"
            f"💰 *Мин. сумма:* {level[3]} руб.\n"
            f"📈 *Бонус:* {level[4]}%\n"
        )
        
        if level[5]:  # Описание
            confirmation_text += f"📝 *Описание:* {level[5]}\n"
        
        confirmation_text += f"\n❌ *Удалить уровень {level[2]}?*"
        
        # Создаем inline-клавиатуру для подтверждения
        confirm_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    Buttons.CONFIRM_DEL_LEV_YES,
                    callback_data=f"{CONFIRM_DELETE_CALLBACK_PREFIX}{level_id}"
                ),
                InlineKeyboardButton(
                    Buttons.CONFIRM_DEL_LEV_NO,
                    callback_data=CANCEL_DELETE_CALLBACK
                )
            ]
        ])
        
        await query.edit_message_text(
            confirmation_text,
            #parse_mode='Markdown',
            reply_markup=confirm_keyboard
        )
    
    # Обработка подтверждения удаления
    elif callback_data.startswith(CONFIRM_DELETE_CALLBACK_PREFIX):
        level_id = int(callback_data.replace(CONFIRM_DELETE_CALLBACK_PREFIX, ""))
        
        # Получаем информацию об уровне перед удалением
        level = bonus_levels_manager.get_bonus_level(level_id)
        level_name = level[2] if level else "неизвестный уровень"
        
        # Удаляем уровень
        if bonus_levels_manager.delete_bonus_level(level_id):
            await query.edit_message_text(
                f"✅ Уровень '{level_name}' успешно удален!",
            )
        # Отправляем отдельное сообщение с клавиатурой
            await query.message.reply_text(
                "Вернуться в меню управления уровнями:",
                reply_markup=await get_levels_management_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка при удалении уровня."
            )
        
        # Очищаем контекст
        context.user_data.pop('level_to_delete_inline', None)

async def delete_level_command_handler(update: Update, context: CallbackContext) -> None:
    """
    Обработчик команды /deletelevel
    Перенаправляет на inline-версию удаления
    """
    await delete_level_inline_handler(update, context)