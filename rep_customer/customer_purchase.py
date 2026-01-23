# handlers/customers_purchase.py
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
import decimal
from config.buttons import Buttons
from keyboards.bonus_keyb import get_confirm_bonus_keyboard
from keyboards.customeers_keyb import get_customers_main_keyboard
from keyboards.global_keyb import get_cancel_keyboard, get_main_keyboard
from handlers.admin_roles_class import role_manager
from .customer_purchase_class import customer_purchase
from utils.telegram_utils import send_or_edit_message

logger = logging.getLogger(__name__)


async def add_purchase(update: Update, context: CallbackContext) -> None:
    """Начало процесса начисления покупки"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if not role_manager.can_manage_customers(role):
        await send_or_edit_message(
            update,
            "⛔ У вас нет прав для начисления покупок.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    context.user_data['adding_purchase'] = {
        'step': 'card_number',
        'data': {}
    }
    
    await send_or_edit_message(
        update,
        "💰 *Начисление покупки клиенту*\n\n"
        "Введите номер карты клиента:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown'
    )


async def process_purchase(update: Update, context: CallbackContext) -> None:
    """Обработка начисления покупки"""
    if 'adding_purchase' not in context.user_data:
        return
    
    text = update.message.text.strip()
    process = context.user_data['adding_purchase']
    step = process['step']
    
    if text == Buttons.CANCEL:
        del context.user_data['adding_purchase']
        await update.message.reply_text(
            "❌ Начисление отменено.",
            reply_markup=await get_customers_main_keyboard()
        )
        return
    
    if step == 'card_number':
        await handle_card_number_step(update, context, text, process)
    
    elif step == 'amount':
        await handle_amount_step(update, context, text, process)
    
    elif step == 'description':
        await handle_description_step(update, context, text, process)
    
    elif step == 'confirm':
        await handle_confirmation_step(update, context, text, process)


async def handle_card_number_step(update: Update, context: CallbackContext, 
                                 text: str, process: dict) -> None:
    """Обработка шага ввода номера карты"""
    try:
        customer = await customer_purchase.find_customer_by_cardprogram(text)
        
        if not customer:
            await update.message.reply_text(
                "❌ Клиент не найден или карта неактивна.\n"
                "Проверьте номер карты и попробуйте снова:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        process['data']['customer'] = customer
        process['step'] = 'amount'
        
        current_bonus = customer_purchase.calculate_current_bonus_percent(
            customer['total_purchases'],
            customer['bonus_program_id']
        )
        
        await update.message.reply_text(
            f"👤 *Клиент:* {customer['username']}\n"
            f"💳 *Карта:* {customer['card_number']}\n"
            f"💰 *Текущие покупки:* {customer['total_purchases']} руб.\n"
            f"📊 *Текущий бонусный %:* {current_bonus}%\n"
            f"🎁 *Доступные бонусы:* {customer.get('available_bonuses', 0):.2f} руб.\n\n"
            "Введите сумму покупки:",
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка поиска клиента: {e}")
        await update.message.reply_text(
            "❌ Ошибка поиска клиента. Попробуйте снова:",
            reply_markup=get_cancel_keyboard()
        )


async def handle_amount_step(update: Update, context: CallbackContext, 
                            text: str, process: dict) -> None:
    """Обработка шага ввода суммы"""
    try:
        amount = decimal.Decimal(text)
        if amount <= 0:
            await update.message.reply_text(
                "Сумма должна быть больше 0. Введите снова:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        customer = process['data']['customer']
        
        bonus_percent = customer_purchase.calculate_current_bonus_percent(
            customer['total_purchases'],
            customer['bonus_program_id']
        )
        
        bonus_amount = customer_purchase.calculate_bonus_amount(amount, bonus_percent)
        
        process['data']['amount'] = str(amount)
        process['data']['bonus_amount'] = str(bonus_amount)
        process['data']['bonus_percent'] = str(bonus_percent)
        process['step'] = 'description'
        
        await update.message.reply_text(
            f"💰 *Сумма покупки:* {amount} руб.\n"
            f"📊 *Начислено бонусов:* {bonus_amount:.2f} руб. ({bonus_percent}%)\n\n"
            "Введите описание покупки (необязательно):\n"
            "Например: 'Кофе латте', 'Десерт чизкейк'\n"
            "Или нажмите 'Пропустить'",
            reply_markup=ReplyKeyboardMarkup(
                [["Пропустить", "❌ Отмена"]],
                resize_keyboard=True
            ),
            parse_mode='Markdown'
        )
        
    except (ValueError, decimal.InvalidOperation):
        await update.message.reply_text(
            "Введите корректную сумму:",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка расчета бонусов: {e}")
        await update.message.reply_text(
            "❌ Ошибка расчета бонусов. Попробуйте снова:",
            reply_markup=get_cancel_keyboard()
        )


async def handle_description_step(update: Update, context: CallbackContext, 
                                 text: str, process: dict) -> None:
    """Обработка шага ввода описания"""
    if text == "Пропустить":
        process['data']['description'] = None
    else:
        process['data']['description'] = text
    
    process['step'] = 'confirm'
    
    confirm_text = (
        "✅ *Подтверждение покупки:*\n\n"
        f"👤 *Клиент:* {process['data']['customer']['username']}\n"
        f"💳 *Карта:* {process['data']['customer']['card_number']}\n"
        f"💰 *Сумма:* {process['data']['amount']} руб.\n"
        f"🎁 *Бонусы:* {process['data']['bonus_amount']} руб. "
        f"({process['data']['bonus_percent']}%)\n"
        f"📝 *Описание:* {process['data']['description'] or 'Не указано'}\n\n"
        "Начислить покупку?"
    )
    
    await update.message.reply_text(
        confirm_text,
        reply_markup=get_confirm_bonus_keyboard(),
        parse_mode='Markdown'
    )


async def handle_confirmation_step(update: Update, context: CallbackContext, 
                                  text: str, process: dict) -> None:
    """Обработка шага подтверждения"""
    if text == Buttons.CONFIRM_YES:
        await save_purchase(update, context, process['data'])
    else:
        del context.user_data['adding_purchase']
        await update.message.reply_text(
            "❌ Начисление отменено.",
            reply_markup=await get_customers_main_keyboard()
        )


async def save_purchase(update: Update, context: CallbackContext, purchase_data: dict) -> None:
    """Сохранение покупки"""
    try:
        operator_telegram_id = update.effective_user.id
        
        # Сохраняем покупку через класс
        purchase_id = await customer_purchase.save_purchase_transaction(
            purchase_data,
            operator_telegram_id
        )
        
        # Получаем обновленную статистику
        updated_stats = await customer_purchase.get_updated_customer_stats(
            purchase_data['customer']['customer_id']
        )
        
        del context.user_data['adding_purchase']
        
        message = (
            f"✅ *Покупка успешно начислена!*\n\n"
            f"👤 *Клиент:* {purchase_data['customer']['username']}\n"
            f"💰 *Сумма покупки:* {purchase_data['amount']} руб.\n"
            f"🎁 *Начислено бонусов:* {purchase_data['bonus_amount']} руб.\n"
            f"📊 *Процент начисления:* {purchase_data['bonus_percent']}%\n"
            f"🆔 *Номер операции:* {purchase_id}\n\n"
        )
        
        if updated_stats:
            message += (
                f"📈 *Итоговые показатели:*\n"
                f"• Общая сумма покупок: {updated_stats.get('total_purchases', 0)} руб.\n"
                f"• Доступные бонусы: {updated_stats.get('available_bonuses', 0):.2f} руб.\n"
            )
        
        await update.message.reply_text(
            message,
            reply_markup=await get_customers_main_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка сохранения покупки: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при сохранении покупки: {str(e)}",
            reply_markup=await get_customers_main_keyboard()
        )