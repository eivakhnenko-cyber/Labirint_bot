"""
Модуль для inline-функциональности клиентов
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from utils.telegram_utils import send_or_edit_message
from config.buttons import Buttons
from keyboards.customeers_keyb import get_customers_main_keyboard

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
INLINE_MODE_KEY = 'inline_mode_active'

def set_inline_mode_active(context: CallbackContext, is_active: bool = True):
    """Установить статус inline-режима"""
    context.user_data[INLINE_MODE_KEY] = is_active

def is_inline_mode_active(context: CallbackContext) -> bool:
    """Проверить активен ли inline-режим"""
    return context.user_data.get(INLINE_MODE_KEY, False)

async def hide_navigation_keyboard_if_inline_active(update: Update, context: CallbackContext) -> bool:
    """
    Проверяет, активен ли inline-режим и скрывает клавиатуру навигации.
    Возвращает True если inline-режим активен (клавиатура скрыта)
    """
    logger.info(f"Начало скрытия клавиатуры")
    
    try:
        # Устанавливаем флаг inline-режима
        set_inline_mode_active(context, True)
        
        # Отправляем новое сообщение с пустой клавиатурой
        # Это скроет предыдущую клавиатуру
        if update.message:
            await update.message.reply_text(
                "⬇️",  # Невидимый символ (zero-width space)
                reply_markup=ReplyKeyboardRemove()  # ← Важно! Используем ReplyKeyboardRemove
            )
            logger.info("Отправили сообщение с ReplyKeyboardRemove")
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                "⬇️",
                reply_markup=ReplyKeyboardRemove()
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка скрытия клавиатуры: {e}")
        set_inline_mode_active(context, True)
        return True
    #     # Отправляем пустое сообщение без клавиатуры (скрываем предыдущую)
    #     await send_or_edit_message(
    #         update,
    #         "_",  # Пустое сообщение
    #         reply_markup=None  # Убираем клавиатуру
    #     )
    #     # Устанавливаем флаг inline-режима
    #     set_inline_mode_active(context, True)
    #     return True
    # except Exception as e:
    #     logger.warning(f"Не удалось скрыть клавиатуру: {e}")
    #     return False

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
        username = customer['username'][:20] + "..." if len(customer['username']) > 20 else customer['username']
        
        # Добавляем информацию в текст
        message_text += (
            f"{i}. *{username}*\n"
            f"   📱 {customer.get('phone_number', 'Нет телефона')}\n"
            f"   🆔 ID: {customer['customer_id']}\n"
        )
        message_text += "\n"
        
        if customer.get('total_purchases', 0) > 0:
            message_text += f"   💰 {customer['total_purchases']} руб.\n"

        # Создаем inline-кнопку
        button_text = f"👤 {customer['customer_id']}: {username}"
        callback_data = f"{VIEW_CUSTOMER_PREFIX}{customer['customer_id']}"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=callback_data)
        ])
    
    # Добавляем кнопку закрытия
    keyboard.append([
        InlineKeyboardButton(Buttons.CLOSE_CUSTOMER_LIST, callback_data=CLOSE_CUSTOMER_LIST)
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
        # Сохраняем список в контексте
    context.user_data[list_key] = customers 

    # Устанавливаем флаг inline-режима
    #set_inline_mode_active(context, True)

    # Отправляем или редактируем сообщение
    if is_editing:
    #Редактируем существующее inline-сообщение
        await query.edit_message_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # Отправляем новое сообщение с inline-кнопками
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

async def handle_close_customer_list(update: Update, context: CallbackContext) -> None:
    """Обработчик закрытия списка клиентов"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        # Сначала сбрасываем флаг inline-режима
        set_inline_mode_active(context, False)
        
        # Очищаем данные списка
        if 'search_results' in context.user_data:
            del context.user_data['search_results']
        if 'all_customers_list' in context.user_data:
            del context.user_data['all_customers_list']
        
        # Пытаемся удалить сообщение
        try:
            await query.delete_message()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
            # Пытаемся редактировать сообщение
            try:
                await query.edit_message_text(
                    "❌ Список закрыт",
                    reply_markup=None
                )
            except Exception as e2:
                logger.warning(f"Не удалось редактировать сообщение: {e2}")
                # Просто выходим если сообщение уже удалено
        
        # Показываем клавиатуру навигации в новом сообщении
        await query.message.reply_text(
            "📋 Список клиентов закрыт.\nВыберите действие:",
            reply_markup=await get_customers_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка закрытия списка клиентов: {e}")
        # Все равно показываем основное меню
        try:
            await query.message.reply_text(
                "📋 Возврат в меню клиентов.\nВыберите действие:",
                reply_markup=await get_customers_main_keyboard()
            )
        except:
            pass

async def handle_close_details(update: Update, context: CallbackContext):
    """Обработчик закрытия деталей клиента"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        # Сбрасываем флаг inline-режима
        set_inline_mode_active(context, False)
        
        # Пытаемся удалить сообщение
        try:
            await query.delete_message()
        except Exception as e:
            logger.warning(f"Не удалось удалить детали: {e}")
            # Пытаемся редактировать сообщение
            try:
                await query.edit_message_text(
                    "❌ Детали закрыты",
                    reply_markup=None
                )
            except Exception as e2:
                logger.warning(f"Не удалось редактировать детали: {e2}")
                # Просто выходим если сообщение уже удалено
        
        # Показываем клавиатуру навигации в новом сообщении
        await query.message.reply_text(
            "👤 Детали клиента закрыты.\nВыберите действие:",
            reply_markup=await get_customers_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка закрытия деталей клиента: {e}")
        # Все равно показываем основное меню
        try:
            await query.message.reply_text(
                "👤 Возврат в меню клиентов.\nВыберите действие:",
                reply_markup=await get_customers_main_keyboard()
            )
        except:
            pass