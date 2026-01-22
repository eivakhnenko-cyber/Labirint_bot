# handlers/callback_handler.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from handlers.catalog import *
from rep_bonus.bonus_levels_delete import handle_delete_level_callback
from keyboards.bonus_keyb import get_levels_management_keyboard

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    """Обработка общих callback-запросов (не относящихся к ConversationHandler)"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    logger.info(f"General callback query received: {callback_data} from user {user_id}")
    
    # Проверяем, не начинается ли callback с префиксов ConversationHandler
    # Добавьте сюда все префиксы, которые используются в ConversationHandler
    conversation_prefixes = [
        'edit_user_',
        'edit_cancel',
        'edit_user_cancel',
        'back_to_user_management',
        'cancel_edit',
    ]
    
    for prefix in conversation_prefixes:
        if callback_data.startswith(prefix):
            logger.info(f"Callback {callback_data} пропущен - для ConversationHandler")
            return  # Пропускаем обработку - это для ConversationHandler
        
    # ... ваш существующий код обработки каталога ...
    if (callback_data.startswith("delete_level_") or 
        callback_data.startswith("confirm_delete_") or 
        callback_data == "cancel_edit_it" or
        callback_data == "cancel_delete"):
        logger.info(f"Callback для удаления уровней - пропускаем в специальный обработчик: {callback_data}")
        # Возвращаем без обработки - будет обработан в bonus_levels.py
        try:
            await handle_delete_level_callback(update, context)
        except Exception as e:
            logger.error(f"Ошибка в обработчике удаления уровней: {e}")
            await query.edit_message_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=await get_levels_management_keyboard()
            )
        return
    if callback_data == "view_customer_":
        from rep_customer.customers import show_customer_list
        await show_customer_list(update, context)

    # Навигация
    if callback_data == "back_to_catalog_menu":
        from handlers.catalog import manage_catalog
        await manage_catalog(update, context)
    
    elif callback_data == "back_to_inventory":
        from rep_invent.inventory import inventory_menu
        await inventory_menu(update, context)
    
    elif callback_data == "back_to_catalog":
        await browse_catalog(update, context)
    
    elif callback_data == "close_menu":
        await query.delete_message()
    
    elif callback_data == "cancel_action":
        await query.edit_message_text(
            "❌ Действие отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
    
    elif callback_data == "other_categories":
        await browse_catalog(update, context)
    
    elif callback_data == "add_product_catalog":
        await add_to_catalog(update, context)

    elif callback_data == "add_product_catalog":
        # Удаляем сообщение с inline-клавиатурой перед переходом
        await query.delete_message()
        await add_to_catalog(update, context)

    elif callback_data == "manage_catalog":
        # Удаляем сообщение с inline-клавиатурой перед переходом
        await query.delete_message()
        await manage_catalog(update, context)

    # Просмотр категорий
    elif callback_data.startswith(CATEGORY_BROWSE_PREFIX):
        category = callback_data[len(CATEGORY_BROWSE_PREFIX):]
        await show_products_by_category(update, context, category)
    
    # Выбор категории для добавления в инвентарь
    elif callback_data.startswith(CATEGORY_SELECT_PREFIX):
        category = callback_data[len(CATEGORY_SELECT_PREFIX):]
        await show_products_by_category(update, context, category)
    
    # Удаление категории
    elif callback_data.startswith(CATEGORY_DELETE_PREFIX):
        category = callback_data[len(CATEGORY_DELETE_PREFIX):]
        await handle_category_deletion(update, context, category)
    
    # Просмотр товара
    elif callback_data.startswith(PRODUCT_VIEW_PREFIX):
        product_id = int(callback_data[len(PRODUCT_VIEW_PREFIX):])
        await show_product_details(update, context, product_id)
    
    # Выбор товара для удаления
    elif callback_data.startswith(PRODUCT_SELECT_PREFIX):
        product_id = int(callback_data[len(PRODUCT_SELECT_PREFIX):])
        await handle_product_deletion_selection(update, context, product_id)
    
    # Удаление всех товаров категории
    elif callback_data == "delete_all_category":
        await handle_delete_all_confirmation(update, context)
    
    # Подтверждение удаления товара
    elif callback_data.startswith(CONFIRM_DELETE_SINGLE):
        product_id = int(callback_data[len(CONFIRM_DELETE_SINGLE):])
        await confirm_delete_product(update, context, product_id)
    
    # Подтверждение удаления всех товаров
    elif callback_data.startswith(CONFIRM_DELETE_ALL):
        category = callback_data[len(CONFIRM_DELETE_ALL):]
        await confirm_delete_all_products(update, context, category)
    
    # Редактирование категории
    elif callback_data.startswith(EDIT_CATEGORY_PREFIX):
        category = callback_data[len(EDIT_CATEGORY_PREFIX):]
        await handle_category_edit_selection(update, context, category)
    
    # Редактирование товара
    elif callback_data.startswith(EDIT_PRODUCT_PREFIX):
        product_id = int(callback_data[len(EDIT_PRODUCT_PREFIX):])
        await handle_product_edit_selection(update, context, product_id)
    
    # Редактирование поля товара
    elif callback_data.startswith(EDIT_FIELD_PREFIX):
        field = callback_data[len(EDIT_FIELD_PREFIX):]
        await handle_field_edit_selection(update, context, field)
    
    # Отмена редактирования категории
    elif callback_data == "cancel_edit_category":
        await query.edit_message_text(
            "❌ Изменение категории отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
    # Отмена редактирования товара
    elif callback_data == "cancel_edit":
        await query.edit_message_text(
            "❌ Редактирование отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
