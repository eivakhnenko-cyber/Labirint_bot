# utils/telegram_utils.py
from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup
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
            # Определяем тип клавиатуры
            is_inline_keyboard = isinstance(reply_markup, InlineKeyboardMarkup)
            is_reply_keyboard = isinstance(reply_markup, ReplyKeyboardMarkup) or reply_markup is None
            
            if delete_previous or is_reply_keyboard:
                # Для обычных клавиатур или при явном указании удаляем старое сообщение
                await update.callback_query.delete_message()
                # Отправляем новое сообщение (БЕЗ reply_to_message_id)
                await update.callback_query.message.chat.send_message(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            elif is_inline_keyboard:
                # Для inline-клавиатур редактируем существующее сообщение
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                # По умолчанию удаляем и отправляем новое
                await update.callback_query.delete_message()
                await update.callback_query.message.chat.send_message(
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
            if update.callback_query:
                # Пытаемся просто отправить сообщение без привязки к удаленному
                await update.callback_query.message.chat.send_message(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                await update.effective_message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        except Exception as e2:
            logger.error(f"Резервный вариант тоже не сработал: {e2}")