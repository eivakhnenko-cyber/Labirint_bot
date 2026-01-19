"""
Модуль для inline-функциональности клиентов
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

# Префиксы callback_data для клиентов
VIEW_CUSTOMER_PREFIX = "view_customer_"
ADD_PURCHASE_PREFIX = "add_purchase_"
EDIT_CUSTOMER_PREFIX = "edit_customer_"
VIEW_HISTORY_PREFIX = "history_"
VIEW_BONUSES_PREFIX = "bonuses_"
CLOSE_CUSTOMER_LIST = "close_customer_list"
BACK_TO_LIST = "back_to_customer_list"
CLOSE_DETAILS = "close_details"

async def show_customer_list_inline(update: Update, context: CallbackContext, customers: list, search_query: str = None) -> None:
    """
    Показать список клиентов ТОЛЬКО с inline-кнопками
    Используется как отдельное сообщение
    """
    if update.callback_query:
        query = update.callback_query
        message = query.message
        is_editing = True
    else:
        query = None
        message = update.message
        is_editing = False
    
    # Формируем текст сообщения
    if search_query:
        message_text = f"🔍 *Найдено клиентов: {len(customers)}*\n"
        message_text += f"*По запросу:* `{search_query}`\n\n"
        list_key = 'search_results'
    else:
        message_text = "👥 *Список клиентов*\n\n"
        message_text += f"*Всего клиентов:* {len(customers)}\n\n"
        list_key = 'all_customers_list'
    
    # Создаем inline-клавиатуру
    keyboard = []
    
    for i, customer in enumerate(customers, 1):
        username = customer['username'][:15] + "..." if len(customer['username']) > 15 else customer['username']
        
        # Добавляем информацию в текст
        message_text += f"{i}. *{username}*\n"
        message_text += f"   📱 {customer.get('phone_number', 'Нет телефона')}\n"
        message_text += f"   🆔 ID: {customer['customer_id']}\n"
        
        if customer.get('total_purchases', 0) > 0:
            message_text += f"   💰 {customer['total_purchases']} руб.\n"
        
        message_text += "\n"
        
        # Создаем inline-кнопку
        button_text = f"👤 {customer['customer_id']}: {username}"
        callback_data = f"{VIEW_CUSTOMER_PREFIX}{customer['customer_id']}"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=callback_data)
        ])
    
    # Добавляем кнопку закрытия
    keyboard.append([
        InlineKeyboardButton("❌ Закрыть", callback_data=CLOSE_CUSTOMER_LIST)
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Сохраняем список в контексте
    context.user_data[list_key] = customers
    
    # Отправляем или редактируем сообщение
    if is_editing:
        await query.edit_message_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await message.reply_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def show_customer_details_inline(query: Update, context: CallbackContext, customer: dict) -> None:
    """Показать детали клиента с inline-кнопками действий"""
    
    # Формируем детальное сообщение
    message_text = f"👤 *Детальная информация*\n\n"
    message_text += f"*Имя:* {customer['username']}\n"
    message_text += f"*ID:* {customer['customer_id']}\n"
    message_text += f"*Телефон:* {customer.get('phone_number', 'Не указан')}\n"
    
    if customer.get('card_number'):
        message_text += f"*Карта:* {customer['card_number']}\n"
    
    if customer.get('email'):
        message_text += f"*Email:* {customer['email']}\n"
    
    if customer.get('registration_date'):
        try:
            date_obj = datetime.strptime(customer['registration_date'], "%Y-%m-%d %H:%M:%S")
            reg_date = date_obj.strftime("%d.%m.%Y %H:%M")
            message_text += f"*Дата регистрации:* {reg_date}\n"
        except:
            message_text += f"*Дата регистрации:* {customer['registration_date']}\n"
    
    message_text += f"*Общая сумма покупок:* {customer.get('total_purchases', 0)} руб.\n"
    message_text += f"*Статус:* {'✅ Активен' if customer.get('is_active', True) else '❌ Неактивен'}\n"
    
    # Создаем inline-кнопки действий
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Добавить покупку", callback_data=f"{ADD_PURCHASE_PREFIX}{customer['customer_id']}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"{EDIT_CUSTOMER_PREFIX}{customer['customer_id']}")
        ],
        [
            InlineKeyboardButton("📋 История", callback_data=f"{VIEW_HISTORY_PREFIX}{customer['customer_id']}"),
            InlineKeyboardButton("🎁 Бонусы", callback_data=f"{VIEW_BONUSES_PREFIX}{customer['customer_id']}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад к списку", callback_data=BACK_TO_LIST),
            InlineKeyboardButton("❌ Закрыть", callback_data=CLOSE_DETAILS)
        ]
    ])
    
    if hasattr(query, 'callback_query'):
        await query.callback_query.edit_message_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await query.edit_message_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )