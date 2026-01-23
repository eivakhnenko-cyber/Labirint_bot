# handlers/customers_register.py
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from datetime import datetime
from database import sqlite_connection
from config.buttons import Buttons
from keyboards.bonus_keyb import get_confirm_bonus_keyboard
from keyboards.customeers_keyb import get_customers_main_keyboard
from keyboards.global_keyb import get_cancel_keyboard, get_main_keyboard
from handlers.admin_roles_class import role_manager, UserRole
from .customer_register_class import customer_register

logger = logging.getLogger(__name__)

async def register_customer(update: Update, context: CallbackContext) -> None:
    """Начало регистрации клиента"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if not role_manager.can_manage_customers(role):
        await update.message.reply_text(
            "⛔ У вас нет прав для регистрации клиентов.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Устанавливаем процесс регистрации
    context.user_data['registering_customer'] = {
        'step': 'username',
        'data': {}
    }
    
    await update.message.reply_text(
        "👤 *Регистрация нового клиента*\n\n"
        "Введите имя клиента:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown'
    )

async def process_customer_registration(update: Update, context: CallbackContext) -> None:
    """Обработка регистрации клиента"""
    user_id = update.effective_user.id
    if 'registering_customer' not in context.user_data:
        return
    
    text = update.message.text.strip()
    process = context.user_data['registering_customer']
    step = process['step']
    
    if text == Buttons.CANCEL:
        del context.user_data['registering_customer']

        await update.message.reply_text(
            "❌ Регистрация отменена.",
            reply_markup=await get_customers_main_keyboard()
        )
        return
    
    if step == 'username':
        if not text:
            await update.message.reply_text("Введите корректное имя:")
            return
        
        process['data']['username'] = text
        process['step'] = 'phone'
        
        await update.message.reply_text(
            "📱 Введите номер телефона клиента:\n"
            "Формат: +7XXXXXXXXXX",
            reply_markup=get_cancel_keyboard()
        )
    
    elif step == 'phone':
        # Простая проверка номера телефона
        phone = text.replace('+', '').replace(' ', '').replace('-', '')
        if not phone.isdigit() or len(phone) < 10:
            await update.message.reply_text(
                "Введите корректный номер телефона (только цифры):",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Форматируем номер
        if phone.startswith('7') and len(phone) == 11:
            phone = f"+7{phone[1:]}"
        elif len(phone) == 10:
            phone = f"+7{phone}"
        else:
            phone = f"+{phone}"
        
        # Проверяем, есть ли уже такой номер
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT customer_id FROM customers WHERE phone_number = ?",
                    (phone,)
                )
                if cursor.fetchone():
                    await update.message.reply_text(
                        "❌ Клиент с таким номером уже зарегистрирован.\n"
                        "Введите другой номер телефона:",
                        reply_markup=get_cancel_keyboard()
                    )
                    return
        except Exception as e:
            logger.error(f"Ошибка проверки номера: {e}")
        
        process['data']['phone'] = phone
        process['step'] = 'birthday'
        
        await update.message.reply_text(
            "🎂 Введите дату рождения клиента (необязательно):\n"
            "Формат: ДД.ММ.ГГГГ\n"
            "Или нажмите 'Пропустить'",
            reply_markup=ReplyKeyboardMarkup(
                [["Пропустить", "❌ Отмена"]],
                resize_keyboard=True
            )
        )
    
    elif step == 'birthday':
        if text == "Пропустить":
            process['data']['birthday'] = None
        else:
            try:
                # Пробуем распарсить дату
                birthday = datetime.strptime(text, "%d.%m.%Y")
                process['data']['birthday'] = birthday.strftime("%Y-%m-%d")
            except ValueError:
                await update.message.reply_text(
                    "Введите дату в формате ДД.ММ.ГГГГ или нажмите 'Пропустить':"
                )
                return
        
        process['step'] = 'confirm'
        
        # Генерируем номер карты
        card_number = customer_register.generate_card_number()
        process['data']['card_number'] = card_number
        
        # Формируем текст подтверждения
        confirm_text = (
            "✅ *Данные для регистрации:*\n\n"
            f"👤 *Имя:* {process['data']['username']}\n"
            f"📱 *Телефон:* {process['data']['phone']}\n"
            f"🎂 *Дата рождения:* {process['data']['birthday'] or 'Не указана'}\n"
            f"💳 *Номер карты:* {card_number}\n\n"
            "Подтвердить регистрацию?"
        )
        
        await update.message.reply_text(
            confirm_text,
            reply_markup=get_confirm_bonus_keyboard(),
            parse_mode='Markdown'
        )
    
    elif step == 'confirm':
        if text == Buttons.CONFIRM_YES:
            await customer_register.save_customer(update, context, process['data'])
        else:
            del context.user_data['registering_customer']
            await update.message.reply_text(
                "❌ Регистрация отменена.",
                reply_markup=await get_customers_main_keyboard()
            )
