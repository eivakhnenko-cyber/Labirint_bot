import os
from telegram import Update
from telegram.ext import CallbackContext
import logging
from datetime import datetime
from handlers.admin_roles_class import role_manager, UserRole
from keyboards.global_keyb import get_main_keyboard
from pathlib import Path
from bot_comands import set_user_commands

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        user_id = user.id
        logo_path = None

         # Устанавливаем персональные команды для пользователя
        await set_user_commands(update, context)
        # Проверяем разные форматы в разных папках
        possible_paths = [
            'logo.jpg', 'logo.jpeg', 'logo.png', 'logo.webp',
            'assets/logo.jpg', 'assets/logo.png',
            'images/logo.jpg', 'images/logo.png'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logo_path = Path(path)
                break

        # Получаем или устанавливаем роль
        role = await role_manager.get_user_role(user_id)
        role_name = role_manager.get_role_name(role)

        guest_text = ""
        welcome_text = ""
        
        if role == UserRole.GUEST:
            guest_text = (
                f"🏰 *Добро пожаловать в Labirint Coffee!* ☕\n\n"
                f"👤 *Пользователь:* {user.first_name}\n"
                f"📅 *Дата:* {datetime.now().strftime('%d.%m.%Y')}\n\n"
            )
            welcome_text = guest_text
        elif role == UserRole.VISITOR: 
            guest_text = (
                f"🏰 *Добро пожаловать в Labirint Coffee!* ☕\n\n"
                f"👤 *Пользователь:* {user.first_name}\n"
                f"📅 *Дата:* {datetime.now().strftime('%d.%m.%Y')}\n\n"
            )
            welcome_text = guest_text
        elif role != UserRole.GUEST or UserRole.VISITOR: 
            welcome_text = (
                    f"👋 Привет, {user.first_name}!\n\n"
                    f"🤖 Я бот - твой друг и помощник Labirint coffee.\n"
                    f"🎭 Ваша роль: {role_name}\n\n"
                    f"Используйте кнопки меню для работы с функциями.\n"
                    f"Для просмотра вашей роли используйте команду /role"
                ) 
        elif role == UserRole.ADMIN:
        # Для администраторов добавляем информацию
                welcome_text += (
                      f"\n\n⚙️ У вас есть доступ к панели администратора.\n"
                      f"Используйте команды:\n"
                      f"/users - список пользователей\n"
                      f"/stats - статистика системы\n"
                      f"/setrole <id> <role> - изменить роль"
                    )
        message_sent = False

        if logo_path and logo_path.exists():
            try:
                with open(logo_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=guest_text,
                        parse_mode='Markdown',
                        reply_markup=await get_main_keyboard(user_id)
                    )
                message_sent = True
            except Exception as e:
                logger.error(f"Ошибка отправки логотипа: {e}")
                # Если не удалось отправить фото, отправляем текстовое приветствие
        # Если логотип не найден или не удалось отправить с ним
        if not message_sent:
            final_text = guest_text if role == UserRole.GUEST or UserRole.VISITOR else welcome_text
            await update.message.reply_text(
                final_text,
                parse_mode='Markdown',
                reply_markup=await get_main_keyboard(user_id)
            )
        
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await update.message.reply_text(
            "Произошла ошибка при запуске бота.",
            reply_markup=await get_main_keyboard(user_id)
        )

def check_and_show_logo():
    """Проверяет наличие логотипа и показывает его"""
    logo_extensions = ['.jpg', '.jpeg', '.png', '.webp']

    for ext in logo_extensions:
        if os.path.exists(f"logo{ext}"):
            print(f"✅ Найден логотип: logo{ext}")
            return f"logo{ext}"
    
    print("⚠️ Логотип не найден. Используется текстовая версия.")
    return None