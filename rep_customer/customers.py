# handlers/customers.py
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from datetime import datetime
from config.buttons import Buttons
from keyboards.bonus_keyb import *
from keyboards.customeers_keyb import get_customers_main_keyboard, get_customers_purch_keyboard,get_customer_search_keyboard
from keyboards.global_keyb import get_cancel_keyboard, get_main_keyboard
from .customer_manager_class import customer_manager
from .customer_purchase_class import customer_purchase
from .customers_inline import show_customer_list_inline, is_inline_mode_active
from utils.telegram_utils import send_or_edit_message
from handlers.admin_roles_class import role_manager

logger = logging.getLogger(__name__)


async def manage_customers(update: Update, context: CallbackContext) -> None:
    """Меню управления клиентами"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    # ПРОВЕРКА: если активен inline-режим, показываем предупреждение
    if is_inline_mode_active(context):
        await send_or_edit_message(
            update,
            "⚠️ У вас открыт список клиентов.\n"
            "Закройте его, используя кнопку '❌ Закрыть' вверху, прежде чем выбрать другое действие.",
            reply_markup=None
        )
        return  # ВЫХОДИМ!

    if not role_manager.can_manage_customers(role):
        await send_or_edit_message(
            update,
            "⛔ У вас нет прав для управления клиентами.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    await send_or_edit_message(
        update,
        "👥 *Управление клиентами*\n\n"
        "Выберите действие:",
        reply_markup=await get_customers_main_keyboard(),
        parse_mode='Markdown'
    )

async def check_customer_status(update: Update, context: CallbackContext) -> None:
    """Начать проверку статуса клиента"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if not role_manager.can_manage_customers(role):
        await send_or_edit_message(
            update,
            "⛔ У вас нет прав для проверки статуса клиентов.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    context.user_data['checking_status'] = {
        'step': 'identifier',
        'data': {}
    }
    
    await send_or_edit_message(
        update,
        "🎯 *Проверка статуса клиента*\n\n"
        "Введите номер карты, телефон или ID клиента:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown'
    )

async def show_customer_details(update: Update, context: CallbackContext, customer: dict) -> None:
    """Показать детальную информацию о клиенте"""
    user_id = update.effective_user.id
    
    if customer is None:
        telegram_id = update.effective_user.id
        customer = await customer_manager.find_customer_by_telegram_id(telegram_id)
        
        if not customer:
            await send_or_edit_message(
                update,
                "❌ *Вы не найдены в базе клиентов.*\n\n"
                "Возможные причины:\n"
                "1. Вы не зарегистрированы как клиент\n"
                "2. Ваш аккаунт клиента неактивен\n\n"
                "Обратитесь к администратору для регистрации.",
                parse_mode='Markdown',
                reply_markup=await get_main_keyboard(user_id)
            )
            return
    
    # Рассчитываем текущий бонусный процент
    current_bonus = customer_purchase.calculate_current_bonus_percent(
        customer['total_purchases'],
        customer['bonus_program_id']
    )
    
    # Форматируем даты
    def format_date(date_str, date_format):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S" if " " in date_str else "%Y-%m-%d")
        except:
            return None
    
    reg_date = format_date(customer['registration_date'], "%Y-%m-%d %H:%M:%S")
    birth_date = format_date(customer['birthday'], "%Y-%m-%d")
    user_reg_date = format_date(customer.get('user_created_at'), "%Y-%m-%d %H:%M:%S")
    
    # Перевод ролей
    role_translation = {
        'GUEST': 'Гость',
        'VISITOR': 'Клиент',
        'BARISTA': 'Бариста',
        'MANAGER': 'Менеджер',
        'ADMIN': 'Администратор'
    }
    
    role_display = role_translation.get(customer.get('role', ''), customer.get('role', ''))
    
    # Формируем сообщение
    message = (
        "👤 *Информация о клиенте*\n\n"
        f"🏷️ *Имя:* {customer['username']}\n"
        f"📱 *Телефон:* {customer.get('phone_number', 'Не указан')}\n"
        f"💳 *Карта:* {customer.get('card_number', 'Не указана')}\n"
    )
    
    if birth_date:
        message += f"🎂 *Дата рождения:* {birth_date.strftime('%d.%m.%Y')}\n"
    
    message += f"🆔 *ID клиента:* {customer['customer_id']}\n"
    
    if customer.get('telegram_id'):
        message += f"🆔 *ID пользователя:* {customer['telegram_id']}\n"
    
    if reg_date:
        message += f"📅 *Дата регистрации:* {reg_date.strftime('%d.%m.%Y')}\n"
    
    if user_reg_date:
        message += f"📅 *Аккаунт создан:* {user_reg_date.strftime('%d.%m.%Y %H:%M')}\n"
    
    if role_display:
        message += f"🎭 *Роль:* {role_display}\n"
    
    message += f"📊 *Статус:* {'✅ Активен' if customer.get('is_active') else '❌ Неактивен'}\n\n"
    message += f"💰 *Общая сумма покупок:* {customer.get('total_purchases', 0)} руб.\n"
    message += f"🏆 *Всего бонусов:* {customer.get('total_bonuses', 0)} руб.\n"
    message += f"🎁 *Доступно бонусов:* {customer.get('available_bonuses', 0)} руб.\n"
    message += f"📈 *Текущий бонусный %:* {current_bonus}%\n"
    
    if customer.get('program_name'):
        message += f"🎪 *Бонусная программа:* {customer['program_name']} ({customer.get('base_percent', 0)}%)\n"
    
    # Сохраняем данные клиента в контекст
    context.user_data['last_searched_customer'] = customer
    
    # Для inline-обработки (например, из списка клиентов) используем inline-функцию
    if update.callback_query:
        # Если это callback от inline-кнопки, используем inline-подход
        from .customers_inline import show_customer_details_inline
        await show_customer_details_inline(update, context, customer)
    else:
        # Если это обычное сообщение, используем обычную клавиатуру
        buttons = []
        
        # Добавляем кнопки для возврата к списку
        if 'search_results' in context.user_data:
            buttons.append([Buttons.BACK_TO_SEARCH_RESULT])
        elif 'all_customers_list' in context.user_data:
            buttons.append([Buttons.BACK_TO_CUSTOMERS_LIST])
        
        keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if buttons else None
        
        await send_or_edit_message(
            update,
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

async def list_all_customers(update: Update, context: CallbackContext) -> None:
    """Показать всех клиентов с использованием inline-подхода"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if not role_manager.can_manage_customers(role):
        await send_or_edit_message(
            update,
            "⛔ У вас нет прав для просмотра списка клиентов.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    if is_inline_mode_active(context):
        await send_or_edit_message(
            update,
            "⚠️ У вас уже открыт список клиентов.\n"
            "Закройте его, используя кнопку '❌ Закрыть' вверху.",
            reply_markup=None  # Не показываем клавиатуру
        )
        return
    try:
        # 1. Получаем клиентов с await
        customers = await customer_manager.get_all_customers()
        
        if not customers:
            await send_or_edit_message(
                update,
                "📭 Нет зарегистрированных клиентов.",
                reply_markup=await get_customers_main_keyboard()
            )
            return
        
        # 2. Показываем inline-сообщение со списком клиентов
        await show_customer_list_inline(update, context, customers)
            
        
    except Exception as e:
        logger.error(f"Ошибка получения списка клиентов: {e}")
        await send_or_edit_message(
            update,
            "❌ Ошибка при загрузке списка клиентов. Попробуйте позже.",
            reply_markup=await get_customers_main_keyboard()
        )

async def show_my_bonuses(update: Update, context: CallbackContext) -> None:
    """Показать бонусы текущего пользователя"""
    telegram_id = update.effective_user.id

    try:
        customer = await customer_manager.find_customer_by_telegram_id(telegram_id)
        logger.info(f"Отображение бонусной для: {telegram_id}")

        if customer:
            await show_customer_details(update, context, customer)
        else:
            await send_or_edit_message(
                update,
                "📝 *Вы не зарегистрированы как клиент.*\n\n"
                "Чтобы участвовать в бонусной программе:\n"
                "1. Обратитесь к администратору\n"
                "2. Пройдите регистрацию как клиент\n"
                "3. Получите бонусную карту",
                reply_markup=await get_main_keyboard(telegram_id),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Ошибка поиска клиента для показа бонусов: {e}")
        await send_or_edit_message(
            update,
            "❌ Ошибка при загрузке данных. Попробуйте позже.",
            reply_markup=await get_main_keyboard(telegram_id)
        )

async def show_my_stat(update: Update, context: CallbackContext) -> None:
    """Показать статистику текущего пользователя"""
    telegram_id = update.effective_user.id

    try:
        customer = await customer_manager.find_customer_by_telegram_id(telegram_id)
        logger.info(f"Отображение статистики для: {telegram_id}")

        if customer:
            await show_customer_details(update, context, customer)
        else:
            await send_or_edit_message(
                update,
                "📝 *Вы не зарегистрированы как клиент.*\n\n"
                "Чтобы участвовать в бонусной программе:\n"
                "1. Обратитесь к администратору\n"
                "2. Пройдите регистрацию как клиент\n"
                "3. Получите бонусную карту",
                reply_markup=await get_main_keyboard(telegram_id),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Ошибка поиска клиента для показа статистики: {e}")
        await send_or_edit_message(
            update,
            "❌ Ошибка при загрузке данных. Попробуйте позже.",
            reply_markup=await get_main_keyboard(telegram_id)
        )