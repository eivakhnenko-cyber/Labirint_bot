import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from keyboards.customeers_keyb import get_customers_main_keyboard
from keyboards.global_keyb import get_main_keyboard
from rep_customer.customer_self_register_service import CustomerSelfRegisterService
from .privacy_policy import privacy_manager

logger = logging.getLogger(__name__)

class CustomerSelfRegisterHandler:
    """Обработчик для самостоятельной регистрации клиентов"""
    
    def __init__(self):
        self.service = CustomerSelfRegisterService()
    
    async def start_self_registration(self, update: Update, context: CallbackContext) -> None:
        """Начинает процесс самостоятельной регистрации"""
        user_id = update.effective_user.id
        
        # Проверяем, согласился ли пользователь с политикой
        if not context.user_data.get('agreed_to_privacy'):
            await update.message.reply_text(
                "Сначала необходимо ознакомиться и согласиться с политикой конфиденциальности.",
                reply_markup=privacy_manager.get_policy_keyboard()
            )
            return
        
        # Очищаем предыдущие данные
        context.user_data.clear()
        context.user_data['self_registering'] = {
            'step': 'phone',
            'data': {
                'telegram_id': user_id,
                'first_name': update.effective_user.first_name,
                'username': update.effective_user.username or update.effective_user.first_name
            }
        }
        
        await update.message.reply_text(
            "📱 *Регистрация в бонусной системе*\n\n"
            "Для регистрации отправьте ваш номер телефона:\n\n"
            "Вы можете:\n"
            "1. Нажать кнопку '📱 Отправить мой номер' (если доступно)\n"
            "2. Отправить номер в формате: +7XXXXXXXXXX\n"
            "3. Отправить номер в формате: 8XXXXXXXXXX",
            parse_mode='Markdown'
        )
    
    async def process_phone_input(self, update: Update, context: CallbackContext) -> None:
        """Обрабатывает ввод номера телефона"""
        user_id = update.effective_user.id
        
        # Проверяем, активен ли процесс регистрации
        if 'self_registering' not in context.user_data:
            return
        
        text = update.message.text.strip()
        
        # Обработка контактного сообщения
        if update.message.contact:
            phone = update.message.contact.phone_number
        else:
            phone = text
        
        # Используем сервис для валидации
        is_available, result = self.service.check_phone_availability(phone)
        
        if not is_available:
            await update.message.reply_text(
                f"❌ {result}\n"
                "Пожалуйста, отправьте другой номер телефона:"
            )
            return
        
        # Сохраняем отформатированный номер
        formatted_phone = result
        context.user_data['self_registering']['data']['phone'] = formatted_phone
        context.user_data['self_registering']['step'] = 'birthday'
        
        await update.message.reply_text(
            "✅ Номер телефона принят!\n\n"
            "🎂 *Шаг 2: Дата рождения* (необязательно)\n\n"
            "Для получения специальных предложений в день рождения, "
            "укажите вашу дату рождения:\n"
            "Формат: ДД.ММ.ГГГГ\n\n"
            "Или нажмите кнопку 'Пропустить'",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup(
                [["Пропустить", "❌ Отмена"]],
                resize_keyboard=True
            )
        )
    
    async def process_birthday_input(self, update: Update, context: CallbackContext) -> None:
        """Обрабатывает ввод даты рождения"""
        text = update.message.text.strip()
        
        if text == "Пропустить":
            context.user_data['self_registering']['data']['birthday'] = None
            await self._complete_registration(update, context)
            return
        
        elif text == "❌ Отмена":
            await self._cancel_registration(update, context)
            return
        
        # Используем сервис для валидации даты
        formatted_birthday = self.service.validate_birthday(text)
        if not formatted_birthday:
            await update.message.reply_text(
                "❌ Неверный формат даты или дата недопустима.\n"
                "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:"
            )
            return
        
        context.user_data['self_registering']['data']['birthday'] = formatted_birthday
        await self._complete_registration(update, context)
    
    async def _complete_registration(self, update: Update, context: CallbackContext) -> None:
        """Завершает регистрацию через сервис"""
        user_data = context.user_data['self_registering']['data']
        telegram_id = user_data['telegram_id']
        
        # Подготавливаем данные
        customer_data = self.service.prepare_customer_data(
            telegram_id=user_data['telegram_id'],
            first_name=user_data['first_name'],
            username=user_data['username'],
            phone=user_data['phone'],
            birthday=user_data.get('birthday')
        )
        
        # Регистрируем клиента через сервис
        success, customer_id, error_message = self.service.register_customer(customer_data)
        
        if not success:
            await update.message.reply_text(
                f"❌ Ошибка регистрации: {error_message}",
                reply_markup=await get_main_keyboard(telegram_id)
            )
            context.user_data.clear()
            return
        
        # Формируем сообщение об успехе
        message = self.service.format_registration_message(customer_data, customer_id)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=await get_main_keyboard(telegram_id)
        )
        
        # Очищаем данные
        context.user_data.clear()
    
    async def _cancel_registration(self, update: Update, context: CallbackContext) -> None:
        """Отменяет регистрацию"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Регистрация отменена.",
            reply_markup=ReplyKeyboardRemove()
        )

# Создаем экземпляр обработчика
customer_self_register = CustomerSelfRegisterHandler()