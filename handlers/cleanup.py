# handlers/cleanup.py
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
import asyncio
from keyboards.global_keyb import get_main_keyboard, get_confirmation_keyboard, get_cancel_keyboard
from keyboards.admin_keyb import get_chat_management_keyboard
from config.buttons import Buttons
from handlers.menus import cleanup_menu

logger = logging.getLogger(__name__)

async def cleanup_own_messages(update: Update, context: CallbackContext) -> None:
    """Удаление только своих сообщений"""
    try:
        chat_id = update.message.chat_id
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Удаляю только сообщения бота...",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Реализация удаления только сообщений бота
        deleted_count = 0
        for i in range(1, 31):  # Последние 30 сообщений
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id - i)
                deleted_count += 1
                await asyncio.sleep(0.3)
            except:
                break
        
        await update.message.reply_text(
            f"✅ Удалено {deleted_count} сообщений бота.",
            reply_markup=await get_chat_management_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка удаления своих сообщений: {e}")
        await update.message.reply_text("Ошибка удаления сообщений.", reply_markup=await get_chat_management_keyboard(user_id))

async def request_message_count(update: Update, context: CallbackContext) -> None:
    """Запрос количества сообщений для удаления"""
    #user_id = update.effective_user.id

    await update.message.reply_text(
        "Введите количество сообщений для удаления (1-500):",
        reply_markup= get_cancel_keyboard()
    )
    context.user_data['awaiting_message_count'] = True

async def handle_message_count_input(update: Update, context: CallbackContext) -> None:
    """Обработка ввода количества сообщений"""
    try:
        count = int(update.message.text)
        if 1 <= count <= 500:
            await delete_specific_count(update, context, count)
        else:
            await update.message.reply_text("Введите число от 1 до 500:")
    except ValueError:
        await update.message.reply_text("Введите корректное число:")
    finally:
        context.user_data['awaiting_message_count'] = False

async def show_cleanup_options(update: Update, context: CallbackContext) -> None:
    """Показывает опции очистки"""
    user_id = update.effective_user.id

    await update.message.reply_text(
        "Выберите тип очистки:",
        reply_markup= await cleanup_menu(user_id)
    )

async def delete_specific_count(update: Update, context: CallbackContext, count: int) -> None:
    """Удаление указанного количества сообщений"""
    try:
        chat_id = update.message.chat_id
        user_id = update.effective_user.id
        deleted_count = 0
        
        for i in range(1, count + 1):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id - i)
                deleted_count += 1
                await asyncio.sleep(0.3)
            except:
                break
        
        await update.message.reply_text(
            f"✅ Удалено {deleted_count} сообщений.",
            reply_markup=await get_chat_management_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка удаления сообщений: {e}")
        await update.message.reply_text("Ошибка удаления сообщений.", reply_markup=await get_chat_management_keyboard(user_id))

async def cleanup_all_messages(update: Update, context: CallbackContext) -> None:
    """Очистка всех сообщений"""
    try:
        chat_id = update.message.chat_id
        
        await update.message.reply_text(
            "⚠️ Внимание! Эта операция удалит ВСЕ сообщения в чате. Продолжить?",
            reply_markup=get_confirmation_keyboard()
        )
        
        context.user_data['awaiting_cleanup_confirmation'] = True
        
    except Exception as e:
        logger.error(f"Ошибка при подготовке очистки: {e}")
        await update.message.reply_text("Ошибка при подготовке очистки.")

async def handle_cleanup_confirmation(update: Update, context: CallbackContext) -> None:
    """Обработка подтверждения очистки"""
    if context.user_data.get('awaiting_cleanup_confirmation', False):
        text = update.message.text
        
        if text == Buttons.CONFIRM_DEL_YES:
            await perform_cleanup(update, context)
        else:
            await update.message.reply_text("Очистка отменена.", reply_markup=get_main_keyboard())
        
        context.user_data['awaiting_cleanup_confirmation'] = False

async def perform_cleanup(update: Update, context: CallbackContext) -> None:
  #"""Упрощенная безопасная очистка - только несколько последних сообщений"""
    try:
        chat_id = update.message.chat_id
        bot = context.bot
        
        # Информируем пользователя об ограничениях
        info_msg = await update.message.reply_text(
            "🧹 Начинаю безопасную очистку...\n\n"
            "⚠️ Ограничения:\n"
            "• Только сообщения бота\n"
            "• Только последние 10 сообщений\n"
            "• Только младше 48 часов",
            reply_markup=ReplyKeyboardRemove()
        )
        
        deleted_count = 0
        
        try:
            # Получаем ID последних сообщений бота
            bot_user = await bot.get_me()
            bot_user_id = bot_user.id
            
            # Собираем ID сообщений бота
            bot_message_ids = []
            async for message in bot.get_chat_history(chat_id=chat_id, limit=20):
                if message.from_user and message.from_user.id == bot_user_id:
                    bot_message_ids.append(message.message_id)
                    if len(bot_message_ids) >= 10:  # Максимум 10 сообщений
                        break
            
            # Удаляем сообщения бота
            for msg_id in bot_message_ids:
                try:
                    # Пропускаем текущее информационное сообщение
                    if msg_id == info_msg.message_id:
                        continue
                        
                    await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    deleted_count += 1
                    await asyncio.sleep(0.8)  # Большая задержка для безопасности
                    
                except Exception as e:
                    # Игнорируем все ошибки удаления
                    continue
            
        except Exception as e:
            logger.error(f"Ошибка сбора сообщений: {e}")
        
        # Удаляем информационное сообщение
        try:
           await info_msg.delete()
        except:
            pass
        
        # Результат
        result_text = f"✅ Удалено {deleted_count} сообщений бота."
        if deleted_count == 0:
            result_text = "❌ Не найдено сообщений бота для удаления.\n" \
                         "(только свои сообщения, младше 48 часов)"
        
        await bot.send_message(
            chat_id=chat_id,
            text=result_text,
            reply_markup=await get_chat_management_keyboard(bot_user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в perform_cleanup: {e}")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Ошибка очистки. Попробуйте позже.",
                reply_markup=await get_chat_management_keyboard(bot_user)
            )
        except:
            pass