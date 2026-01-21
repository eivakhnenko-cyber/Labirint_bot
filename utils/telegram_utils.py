# utils/telegram_utils.py
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging

logger = logging.getLogger(__name__)

async def send_or_edit_message(
    update: Update, 
    text: str, 
    reply_markup=None, 
    parse_mode=None,
    delete_previous: bool = False
) -> None:
    """
    Универсальная функция для отправки/редактирования сообщений.
    
    Args:
        update: Объект Update от Telegram
        text: Текст сообщения
        reply_markup: Разметка клавиатуры
        parse_mode: Режим парсинга (Markdown, HTML)
        delete_previous: Удалить предыдущее сообщение (только для callback -> message)
    """
    try:
        if update.callback_query:
            if delete_previous:
                # Удаляем сообщение с inline-клавиатурой
                await update.callback_query.delete_message()
                # Отправляем новое сообщение
                await update.callback_query.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                # Редактируем существующее сообщение
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        else:
            # Отправляем новое сообщение
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except Exception as e:
        logger.error(f"Ошибка в send_or_edit_message: {e}")
        # Резервный вариант
        try:
            await update.effective_message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e2:
            logger.error(f"Резервный вариант тоже не сработал: {e2}")