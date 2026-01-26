# handlers/admin_edit_user_flow.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.admin_roles_class import role_manager, Permission
from handlers.admin_users_class import users_manager
from keyboards.admin_keyb import get_user_management_keyboard, EditUserStep
from config.buttons import Buttons

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
EDIT_SELECT_USER, EDIT_SELECT_FIELD, EDIT_ENTER_VALUE, EDIT_CONFIRM = range(4)

# Словарь для хранения временных данных
edit_user_data = {}

async def start_edit_user_flow(update: Update, context: CallbackContext) -> int:
    """Начинает процесс редактирования пользователя"""
    user_id = update.effective_user.id
    try:
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text("❌ У вас нет прав для редактирования пользователей.")
            return ConversationHandler.END
        
        # Устанавливаем состояние в контексте для message_handler
        context.user_data['edit_user_state'] = EDIT_SELECT_USER
        
        # Спрашиваем ID пользователя
        await update.message.reply_text(
            "✏️ *Редактирование пользователя*\n\n"
            "Введите ID пользователя для редактирования:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(Buttons.EDIT_USER_CANCEL, callback_data="edit_cancel")]])
        )  
        return EDIT_SELECT_USER
    
    except Exception as e:
        logger.error(f"Ошибка в start_edit_user_flow: {e}")
        return ConversationHandler.END
    
async def select_user_for_edit(update: Update, context: CallbackContext) -> int:
    """Обрабатывает ввод ID пользователя"""
    logger.info(f"select_user_for_edit вызван, user_data: {context.user_data}")
    try:
        if update.callback_query and update.callback_query.data == 'edit_cancel':
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("❌ Редактирование отменено.")
             # Очищаем состояние
            context.user_data.pop('edit_user_state', None)
            return ConversationHandler.END
        
        # Получаем ID пользователя из сообщения
        if update.message:
            try:
                target_user_id = int(update.message.text)
                
                # Проверяем существование пользователя
                existing_role = await role_manager.get_user_role(target_user_id)
                if not existing_role:
                    await update.message.reply_text(
                        f"❌ Пользователь {target_user_id} не найден в системе.",
                        reply_markup=get_user_management_keyboard()
                    )
                    # Очищаем состояние
                    context.user_data.pop('edit_user_state', None)
                    return ConversationHandler.END
                
                # Сохраняем ID пользователя в контексте
                context.user_data['edit_user_state'] = EDIT_SELECT_FIELD
                context.user_data['edit_target_id'] = target_user_id
                
                # Получаем текущую информацию о пользователе
                users = await users_manager.get_all_users()
                user_info = next((u for u in users if u['user_id'] == target_user_id), None)
                
                if user_info:
                    message = f"👤 *Пользователь:* {target_user_id}\n"
                    message += f"📛 *Имя:* {user_info.get('first_name', 'Не указано')}\n"
                    message += f"📛 *Фамилия:* {user_info.get('last_name', 'Не указано')}\n"
                    message += f"👤 *Username:* {user_info.get('username', 'Не указан')}\n"
                    message += f"📱 *Телефон:* {user_info.get('phone_numb', 'Не указан')}\n\n"
                    message += "Выберите поле для редактирования:"
                else:
                    message = f"👤 Пользователь: {target_user_id}\n\nВыберите поле для редактирования:"
                
                # Исправьте эту строку - убираем await
                reply_markup = EditUserStep.get_edit_user_field_keyboard(target_user_id)  # БЕЗ await!
                
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                # КРИТИЧЕСКИ ВАЖНО: Возвращаем следующее состояние
                logger.info(f"Возвращаем состояние EDIT_SELECT_FIELD: {EDIT_SELECT_FIELD}")
                return EDIT_SELECT_FIELD  # <-- ВОЗВРАЩАЕМ СОСТОЯНИЕ!
                
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID. Введите число:")
                # Возвращаем то же состояние для повторного ввода
                return EDIT_SELECT_USER  # <-- ВОЗВРАЩАЕМ ТО ЖЕ СОСТОЯНИЕ
    
    except Exception as e:
        logger.error(f"Ошибка в select_user_for_edit: {e}")
        await update.message.reply_text("❌ Ошибка обработки запроса.")
        return ConversationHandler.END
    
    return EDIT_SELECT_USER

async def select_field_for_edit(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор поля для редактирования"""
    logger.info(f"select_field_for_edit вызван с callback_data: {update.callback_query.data}")
    try:
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Обработка callback: {query.data}")
        
        if query.data == 'back_to_user_management':
            await query.edit_message_text("❌ Редактирование отменено.")
            return ConversationHandler.END
        
        # Извлекаем данные из callback_data
        if query.data.startswith('edit_user_field_'):
            try:
                # Удаляем префикс 'edit_user_field_'
                data_without_prefix = query.data[len('edit_user_field_'):]
                logger.info(f"Данные без префикса: {data_without_prefix}")
                
                # Разделяем по последнему '_' чтобы отделить user_id и field
                # Формат: {user_id}_{field}
                # Для phone_number: 296169859_phone_number
                parts = data_without_prefix.split('_')
                logger.info(f"Разбиваем на части: {parts}")
                
                # Первая часть - user_id
                target_user_id = int(parts[0])
                
                # Все остальное - название поля (может содержать подчеркивания)
                field = '_'.join(parts[1:]) if len(parts) > 1 else ''
                
                logger.info(f"Извлечено: user_id={target_user_id}, field={field}")
                
                if not field:
                    raise ValueError("Не найдено название поля")
                
                # Сохраняем в контексте
                context.user_data['edit_field'] = field
                context.user_data['edit_target_id'] = target_user_id
                context.user_data['edit_user_state'] = EDIT_ENTER_VALUE
                
                # Определяем русское название поля
                field_names = {
                    'username': '👤 Username',
                    'first_name': '📛 First Name', 
                    'last_name': '📛 Last Name',
                    'phone_numb': '📱 Phone Number'
                }
                
                field_name = field_names.get(field, field)
                
                await query.edit_message_text(
                    f"✏️ *Редактирование поля:* {field_name}\n"
                    f"👤 *Пользователь:* {target_user_id}\n\n"
                    f"Введите новое значение для этого поля:",
                    parse_mode='Markdown'
                )
                
                logger.info(f"Возвращаем состояние EDIT_ENTER_VALUE: {EDIT_ENTER_VALUE}")
                return EDIT_ENTER_VALUE
                
            except (ValueError, IndexError) as parse_error:
                logger.error(f"Ошибка разбора callback_data '{query.data}': {parse_error}")
                await query.edit_message_text("❌ Ошибка обработки запроса.")
                return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в select_field_for_edit: {e}")
        await query.edit_message_text("❌ Ошибка выбора поля.")
        return ConversationHandler.END
    
    # Если callback не обработан
    logger.warning(f"Необработанный callback: {query.data}")
    return EDIT_SELECT_FIELD

async def enter_new_value(update: Update, context: CallbackContext) -> int:
    """Обрабатывает ввод нового значения"""
    try:
        if update.message:
            new_value = update.message.text
            target_user_id = context.user_data.get('edit_target_id')
            field = context.user_data.get('edit_field')
            
            logger.info(f"Получены данные: user_id={target_user_id}, field={field}, value={new_value}")

            if not target_user_id or not field:
                await update.message.reply_text("❌ Ошибка: данные не найдены.")
                return ConversationHandler.END
            
            # Сохраняем новое значение
            context.user_data['edit_new_value'] = new_value
            
            # Определяем русское название поля
            field_names = {
                'username': 'Username',
                'first_name': 'First Name', 
                'last_name': 'Last Name',
                'phone_numb': 'Phone Number'
            }
            
            field_name = field_names.get(field, field)
            
            await update.message.reply_text(
                f"✏️ *Подтвердите изменение*\n\n"
                f"👤 *Пользователь:* {target_user_id}\n"
                f"📋 *Поле:* {field_name}\n"
                f"🆕 *Новое значение:* {new_value}\n\n"
                f"Вы уверены, что хотите сохранить эти изменения?",
                parse_mode='Markdown',
                reply_markup=EditUserStep.get_edit_user_confirm_keyboard(target_user_id, field, new_value)
            )
            logger.info(f"Возвращаем состояние EDIT_CONFIRM: {EDIT_CONFIRM}")
            return EDIT_CONFIRM
    
    except Exception as e:
        logger.error(f"Ошибка в enter_new_value: {e}")
        await update.message.reply_text("❌ Ошибка обработки значения.")
        return ConversationHandler.END
    
    return EDIT_ENTER_VALUE

async def confirm_edit(update: Update, context: CallbackContext) -> int:
    """Подтверждает редактирование"""
    logger.info(f"confirm_edit вызван с callback_data: {update.callback_query.data}")
    
    try:
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Обрабатываем callback: {query.data}")
        
        if query.data == 'edit_user_cancel':
            await query.edit_message_text("❌ Редактирование отменено.")
            return ConversationHandler.END
        
        if query.data.startswith('edit_user_confirm_'):
            logger.info(f"Начинаем обработку подтверждения: {query.data}")
            
            try:
                # Удаляем префикс 'edit_user_confirm_'
                data_without_prefix = query.data[len('edit_user_confirm_'):]
                logger.info(f"Данные без префикса: {data_without_prefix}")
                
                # Разделяем по первому '_' после user_id
                # Формат: {user_id}_{field}_{value}
                parts = data_without_prefix.split('_')
                logger.info(f"Разбиваем на части: {parts}")
                
                if len(parts) < 2:
                    raise ValueError("Недостаточно частей в callback_data")
                
                # Первая часть - user_id
                target_user_id = int(parts[0])
                
                # Пытаемся определить поле
                # Список возможных полей
                possible_fields = ['username', 'first_name', 'last_name', 'phone_numb']
                
                field = None
                value_start_index = None
                
                # Пробуем найти поле в начале оставшихся частей
                remaining_parts = '_'.join(parts[1:])
                
                for field_name in possible_fields:
                    if remaining_parts.startswith(field_name + '_') or remaining_parts == field_name:
                        field = field_name
                        # Вычисляем где начинается значение
                        field_parts_count = len(field_name.split('_'))
                        value_start_index = 1 + field_parts_count
                        break
                
                # Если не нашли стандартное поле
                if not field:
                    # Берем следующую часть как поле (простой случай)
                    field = parts[1]
                    value_start_index = 2
                
                # Извлекаем значение
                if value_start_index is not None and len(parts) > value_start_index:
                    new_value = '_'.join(parts[value_start_index:])
                else:
                    new_value = ''
                
                # Заменяем обратно пробелы
                new_value = new_value.replace('_', ' ')
                
                logger.info(f"Извлечено: user_id={target_user_id}, field={field}, value={new_value}")
                
                # Выполняем обновление
                logger.info(f"Вызываем update_user_info для {target_user_id}")
                success = await users_manager.update_user_info(target_user_id, **{field: new_value})
                
                logger.info(f"Результат update_user_info: {success}")
                
                if success:
                    # Экранируем специальные символы для безопасного отображения
                    from telegram.helpers import escape_markdown
                    
                    # Используем escape_markdown для безопасного форматирования
                    safe_user_id = escape_markdown(str(target_user_id), version=2)
                    safe_field = escape_markdown(field.replace('_', ' ').title(), version=2)
                    safe_value = escape_markdown(new_value, version=2)
                    
                    # Отправляем с MarkdownV2 и экранированием
                    await query.edit_message_text(
                        f"✅ Пользователь `{safe_user_id}` успешно обновлен\!\n"
                        f"📋 *Поле:* {safe_field}\n"
                        f"🆕 *Новое значение:* `{safe_value}`",
                        parse_mode='MarkdownV2'
                    )
                    logger.info("Сообщение об успешном обновлении отправлено")
                else:
                    await query.edit_message_text("❌ Не удалось обновить пользователя.")
                    logger.info("Сообщение об ошибке отправлено")
                
                # Очищаем данные
                context.user_data.clear()
                logger.info("Данные очищены")
                
                return ConversationHandler.END
                
            except Exception as parse_error:
                logger.error(f"Ошибка при обработке подтверждения: {parse_error}")
                await query.edit_message_text("❌ Ошибка обработки подтверждения.")
                return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в confirm_edit: {e}")
        # Пробуем отправить простое сообщение об ошибке
        try:
            await query.edit_message_text("❌ Ошибка сохранения изменений.")
        except:
            pass
        return ConversationHandler.END
    
    logger.warning(f"Необработанный callback в confirm_edit: {query.data}")
    return EDIT_CONFIRM

async def cancel_edit(update: Update, context: CallbackContext) -> int:
    """Отменяет процесс редактирования"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Редактирование отменено.")
    
    # Очищаем данные
    if 'edit_flow' in context.user_data:
        del context.user_data['edit_flow']
    
    return ConversationHandler.END

# Создаем ConversationHandler
edit_user_conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex('^✏️ Изменить пользователя$'), start_edit_user_flow)
    ],
    states={
        EDIT_SELECT_USER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, select_user_for_edit),
            CallbackQueryHandler(cancel_edit, pattern='^edit_cancel$')
        ],
        EDIT_SELECT_FIELD: [
            CallbackQueryHandler(select_field_for_edit, pattern='^edit_user_field_'),
            CallbackQueryHandler(cancel_edit, pattern='^back_to_user_management$')
        ],
        EDIT_ENTER_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_new_value)
        ],
        EDIT_CONFIRM: [
            CallbackQueryHandler(confirm_edit, pattern='^edit_user_confirm_.*'),
            CallbackQueryHandler(cancel_edit, pattern='^edit_user_cancel$')
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_edit, pattern='^cancel'),
        CallbackQueryHandler(cancel_edit, pattern='^edit_cancel$'),
        CallbackQueryHandler(cancel_edit, pattern='^back_to_user_management$')
    ],
    allow_reentry=True
)