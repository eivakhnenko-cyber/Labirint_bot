import logging
from telegram import Update, CallbackQuery
from telegram.ext import CallbackContext
from .customer_manager_class import customer_manager
from handlers.admin_roles_class import role_manager
from utils.telegram_utils import send_or_edit_message
from keyboards.customeers_keyb import get_customer_search_keyboard, get_customers_purch_keyboard, get_customers_main_keyboard
from keyboards.global_keyb import get_main_keyboard, get_cancel_keyboard
from config.buttons import Buttons
from rep_customer.customers_inline import show_customer_list_inline

logger = logging.getLogger(__name__)

class SearchManager:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def search_customer(self, update: Update, context: CallbackContext) -> None:
        """Начать поиск клиента"""
        user_id = update.effective_user.id
        role = await role_manager.get_user_role(user_id)
        
        if not role_manager.can_manage_customers(role):
            await send_or_edit_message(
                update,
                "⛔ У вас нет прав для поиска клиентов.",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
        
        context.user_data['searching_customer'] = {
            'step': 'search_input',
            'data': {}
        }
        
        await send_or_edit_message(
            update,
            "🔍 *Поиск клиента*\n\n"
            "Введите:\n"
            "• Номер карты (например: LBC-1234-5678-9012)\n"
            "• Номер телефона\n"
            "• Имя клиента\n\n"
            "Или введите '❌ Отмена' для выхода",
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
    async def search_cust_by_card(self, update: Update, context: CallbackContext) -> None:
        """Начать поиск по карте"""
        await self._start_specific_search(update, context, "card", "💳 *Поиск клиента по карте*\n\nВведите номер карты:")

    async def search_cust_by_id(self, update: Update, context: CallbackContext) -> None:
        """Начать поиск по ID"""
        await self._start_specific_search(update, context, "id", "🆔 *Поиск клиента по ID*\n\nВведите ID клиента:")

    async def search_cust_by_phone(self, update: Update, context: CallbackContext) -> None:
        """Начать поиск по телефону"""
        await self._start_specific_search(update, context, "phone", "📱 *Поиск клиента по телефону*\n\nВведите номер телефона:")

    async def search_cust_by_name(self, update: Update, context: CallbackContext) -> None:
        """Начать поиск по имени"""
        await self._start_specific_search(update, context, "name", "👤 *Поиск клиента по имени*\n\nВведите имя клиента:")
    
    async def _start_specific_search(self, update: Update, context: CallbackContext, search_type: str, message: str):
        """Общий метод для начала конкретного типа поиска"""
        user_id = update.effective_user.id
        role = await role_manager.get_user_role(user_id)
        
        if not role_manager.can_manage_customers(role):
            await send_or_edit_message(
                update,
                "⛔ У вас нет прав для поиска клиентов.",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
        
        context.user_data['searching_customer'] = {
            'step': 'specific_search',
            'type': search_type,
            'data': {}
        }
        
        await send_or_edit_message(
            update,
            f"{message}\n\nИли введите '❌ Отмена' для выхода",
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
        
    async def process_customer_search(self, update: Update, context: CallbackContext) -> None:
        """Обработка поиска клиента"""
        if 'searching_customer' not in context.user_data:
            return
        
        text = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Проверяем отмену
        if text == Buttons.CANCEL:
            del context.user_data['searching_customer']
            await send_or_edit_message(
                update,
                "❌ Поиск отменен.",
                reply_markup=await get_customer_search_keyboard()
            )
            return
        
        # Проверяем inline-режим
        from rep_customer.customers_inline import is_inline_mode_active
        if is_inline_mode_active(context):
            await send_or_edit_message(
                update,
                "⚠️ У вас уже открыт список клиентов.\n"
                "Закройте его, используя кнопку '❌ Закрыть' вверху, прежде чем начать новый поиск.",
                reply_markup=None
            )
            return
        
        try:
            # Определяем тип поиска
            search_type = context.user_data['searching_customer'].get('type', 'general')
            customers = []
            
            if search_type == 'card':
                customers = await customer_manager.find_customer_by_card(text)
            elif search_type == 'id':
                customers = await customer_manager.find_customer_by_id(text)
                if customers:
                    customers = [customers]  # Преобразуем в список для единообразия
            elif search_type == 'phone':
                customers = await customer_manager.find_customers_by_search_query(text)
            elif search_type == 'name':
                customers = await customer_manager.find_customers_by_search_query(text)
            else:
                # Общий поиск
                customers = await customer_manager.find_customers_by_search_query(text)
            
            # Обрабатываем результаты
            if not customers or (isinstance(customers, dict) and not customers):
                await send_or_edit_message(
                    update,
                    "❌ Клиенты не найдены. Попробуйте другой запрос:",
                    reply_markup=get_cancel_keyboard()
                )
                return
            
            del context.user_data['searching_customer']
            
            # Преобразуем одиночного клиента в список если нужно
            if isinstance(customers, dict):
                customers = [customers]
            
            # Перед показом результатов поиска добавьте:
            from rep_customer.customers_inline import hide_navigation_keyboard_if_inline_active
            await hide_navigation_keyboard_if_inline_active(update, context)

            # Используем inline-подход для отображения результатов
            await show_customer_list_inline(update, context, customers, search_query=text)
            
        except Exception as e:
            logger.error(f"Ошибка поиска клиента: {e}", exc_info=True)
            await send_or_edit_message(
                update,
                "❌ Ошибка при поиске клиента. Попробуйте позже.",
                reply_markup=await get_customer_search_keyboard()
            )

# Создаем глобальный экземпляр
search_manager = SearchManager()