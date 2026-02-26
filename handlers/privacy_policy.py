import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode
from utils.telegram_utils import send_or_edit_message

logger = logging.getLogger(__name__)

class PrivacyPolicyManager:
    """Менеджер политики конфиденциальности"""
    
    def __init__(self):
        self.policy_file = "privacy_policy.html"
        self.policy_text = self._load_policy_text()
    
    def _load_policy_text(self) -> str:
        """Загружает текст политики из файла"""
        try:
            # Пробуем найти файл в разных местах
            possible_paths = [
                self.policy_file,
                f"assets/{self.policy_file}",
                f"data/{self.policy_file}",
                f"config/{self.policy_file}"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            # Если файл не найден, возвращаем дефолтный текст
            logger.warning("Файл политики конфиденциальности не найден, используется дефолтный текст")
            return self._get_default_policy_text()
            
        except Exception as e:
            logger.error(f"Ошибка загрузки политики конфиденциальности: {e}")
            return self._get_default_policy_text()
    
    def _get_default_policy_text(self) -> str:
        """Возвращает дефолтный текст политики"""
        return """
                <b>Политика конфиденциальности Labirint Coffee</b>

                <b>1. Общие положения</b>
                Настоящая Политика конфиденциальности регулирует порядок обработки и защиты персональных данных пользователей бота Labirint Coffee.

                <b>2. Собираемые данные</b>
                Мы собираем следующие данные:
                • Имя пользователя
                • Номер телефона
                • Дата рождения (по желанию)
                • История покупок
                • Бонусные баллы

                <b>3. Цели сбора данных</b>
                Данные собираются для:
                • Предоставления услуг бонусной программы
                • Информирования о специальных предложениях
                • Улучшения качества обслуживания

                <b>4. Защита данных</b>
                Мы принимаем меры для защиты ваших персональных данных от несанкционированного доступа.

                <b>5. Согласие на обработку</b>
                Нажимая кнопку "Согласен", вы даете согласие на обработку ваших персональных данных.
                """
    
    def get_policy_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для политики"""
        keyboard = [
            [
                InlineKeyboardButton("📄 Ознакомиться с политикой", callback_data="show_privacy_policy")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_agreement_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру согласия с политикой"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Согласен", callback_data="agree_privacy_policy"),
                InlineKeyboardButton("❌ Отказаться", callback_data="decline_privacy_policy")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_phone_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для отправки номера телефона"""
        keyboard = [
            [
                InlineKeyboardButton("📱 Отправить номер телефона", callback_data="send_phone_number")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def show_privacy_policy(self, update: Update, context: CallbackContext) -> None:
        """Показывает политику конфиденциальности"""
        query = update.callback_query
        await query.answer()
        
        await send_or_edit_message(
            update,
            text=self.policy_text,
            parse_mode=ParseMode.HTML,
            reply_markup=self.get_agreement_keyboard()
        )
    
    async def handle_privacy_callback(self, update: Update, context: CallbackContext) -> None:
        """Обрабатывает callback'и связанные с политикой"""
        query = update.callback_query
        data = query.data
        
        if data == "show_privacy_policy":
            await self.show_privacy_policy(update, context)
        
        elif data == "agree_privacy_policy":
            await send_or_edit_message(
                update,
                text="✅ Вы согласились с политикой конфиденциальности.\n\n"
                     "Для завершения регистрации, пожалуйста, отправьте ваш номер телефона:",
                reply_markup=self.get_phone_keyboard()
            )
            # Устанавливаем флаг, что пользователь согласился
            context.user_data['agreed_to_privacy'] = True
        
        elif data == "decline_privacy_policy":
            await send_or_edit_message(
                update,
                text="❌ Вы отказались от политики конфиденциальности.\n"
                     "Регистрация невозможна без согласия на обработку персональных данных."
            )
            context.user_data.clear()
        
        elif data == "send_phone_number":
            await send_or_edit_message(
                update,
                text="📱 Пожалуйста, отправьте ваш номер телефона одним из способов:\n\n"
                     "1. Нажмите кнопку '📱 Отправить мой номер' (если доступно)\n"
                     "2. Отправьте номер в формате: +7XXXXXXXXXX\n"
                     "3. Отправьте номер в формате: 8XXXXXXXXXX"
            )
            from phone_sharing import request_phone_number
            
            await request_phone_number(context)

            context.user_data.clear()
            # Устанавливаем состояние ожидания номера телефона
            context.user_data['awaiting_phone'] = True
            context.user_data['step'] = 'phone'

# Создаем экземпляр менеджера
privacy_manager = PrivacyPolicyManager()