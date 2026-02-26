from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

async def request_phone_number(update: Update, context: CallbackContext) -> None:
    """Запрашивает номер телефона с кнопкой"""
    keyboard = [
        [KeyboardButton("📱 Отправить мой номер", request_contact=True)],
        ["❌ Отмена"]
    ]
    
    await update.message.reply_text(
        "Для регистрации необходимо предоставить номер телефона.\n\n"
        "Нажмите кнопку ниже, чтобы поделиться номером:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )