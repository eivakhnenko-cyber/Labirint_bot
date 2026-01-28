"""
Улучшенный обработчик сообщений с маршрутизацией
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from router import router

from keyboards.global_keyb import get_main_keyboard
from handlers.cleanup import handle_cleanup_confirmation, handle_message_count_input
from handlers.reminders import (
    handle_schedule_day_selection, handle_time_input,
    handle_custom_reminder_input, handle_reminder_type_selection, check_jobs
)
from handlers.admin import (
    manage_users_menu
)
from handlers.admin_roles import (
    manage_roles_menu
)
from handlers.admin_edit_user_flow import (
    start_edit_user_flow, edit_user_conversation_handler, cancel_edit
)
from handlers.handlers_customer import (
    hand_cust_manager
)
from rep_customer.customers import (
    process_customer_search,
    show_my_bonuses, check_customer_status
)
from rep_customer.customer_purchase import (
    process_purchase
)
from rep_customer.customer_register import (
    process_customer_registration
)
from rep_customer.customer_register_class import customer_register

from rep_invent.inventory import process_item_input, _process_unit

from rep_bonus.bonus_master import ( 
    process_program_creation, manage_bonus_programs, 
)

from handlers.handlers_bonus_levels import (
    list_levels_handler, select_program_handler,
    edit_level_handler, level_statistics_handler, delete_level_handler,
    confirm_delete_level_handler
)
from rep_catalog.catalog_process import (
    CatalogProcessManager
)
from rep_report.report_watch import report_manager

from handlers.callback_handler import handle_callback_query

from config.buttons import Buttons

logger = logging.getLogger(__name__)

class MessageHandler:
    """Обработчик сообщений с маршрутизацией"""
    
    def __init__(self, handlers_registry):
        """Инициализация с реестром обработчиков"""
        self.handlers = handlers_registry
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной обработчик сообщений"""
        text = update.message.text.strip()
        user_id = update.effective_user.id
        
        logger.info(f"Получено сообщение: {text}")
        
        # 1. Проверяем все активные процессы
        handler_result = await self._check_active_processes(update, context, text)
        if handler_result:
            return
        
        # 2. Проверяем навигационные кнопки в списках
        if await self._handle_list_navigation(update, context, text):
            return
        
        # 3. Маршрутизация через роутер
        handler_name = await router.route(update, context, text)
        
        if handler_name:
            if handler_name in self.handlers:
                await self.handlers[handler_name](update, context)
            else:
                logger.warning(f"Обработчик {handler_name} не найден в реестре")
                await self._show_main_menu(user_id)
        else:
            logger.error(f"Что то не то: {text}")

            # Неизвестная команда - показываем главное меню
            await self._cleanup_context(context)
            await self._show_main_menu(user_id)
    
    async def _check_active_processes(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     text: str) -> bool:
        """Проверить активные процессы"""
        user_data = context.user_data
        
        if 'edit_user_state' in user_data:
        # Если у нас активен процесс редактирования пользователя
            return await self._handle_edit_user_process(update, context, text)
        # Список активных процессов и их обработчиков
        processes = [
            # Процессы работы с клиентами
            ('registering_customer', process_customer_registration),
            ('awaiting_generate_card', customer_register.generate_card_number),
            ('check_customer_status', check_customer_status),
            ('adding_purchase', process_purchase),
            ('searching_customer', process_customer_search),
            ('show_my_bonuses', show_my_bonuses),

            # Процессы работы с бонусной системой
            ('creating_program', process_program_creation),
            ('awaiting_manage_program', manage_bonus_programs),
            #('create_level_conversation', create_level_conversation),
            ('selected_program', select_program_handler),
            ('awaiting_list_levels_handler', list_levels_handler),
            ('awaiting_edit_level_handler', edit_level_handler),
            ('awaiting_level_statistics_handler', level_statistics_handler),
            ('awaiting_delete_id', delete_level_handler),
            ('level_to_delete', confirm_delete_level_handler),

            # процессы с работой с напоминаниями
            
            ('awaiting_custom_reminder', handle_custom_reminder_input),
            ('awaiting_schedule_day', handle_schedule_day_selection),
            ('awaiting_reminder_type', handle_reminder_type_selection),
            ('awaiting_schedule_time', handle_time_input),
            ('selected_day', handle_time_input),
            ('return_to_schedule', handle_reminder_type_selection),
            ('check_jobs', check_jobs),
            
            # Процессы с работой инвентарицзации
            ('item_process', process_item_input), # обработка ввода даннных товара
            ('adding_item_method', process_item_input),  # обработка ввода даннных
            ('selected_product', _process_unit),  # обработка единицы измерения
            ('editing_catalog', handle_callback_query), # процесс редактирования товара (использует process_edit_catalog)
            ('editing_category', CatalogProcessManager.process_edit_catalog), # процесс изменения категории (использует process_edit_category)
            ('selected_category', CatalogProcessManager.process_edit_category), # процесс выбора товара из каталога (использует browse_catalog_for_selection)
            ('catalog_products', CatalogProcessManager.process_catalog_addition),
            ('adding_to_catalog', CatalogProcessManager.process_catalog_addition), # процесс добавления товара (использует process_catalog_addition)
            ('deleting_from_catalog', CatalogProcessManager.process_catalog_deletion), # процесс удаления товара (использует process_catalog_deletion)
            ('cancel_edit_it', handle_callback_query),
            
            # Процессы по работе с администрированием

            ('awaiting_message_count', handle_message_count_input),
            ('awaiting_cleanup_confirmation', handle_cleanup_confirmation),
            ('manage_users_menu', manage_users_menu), #
            ('manage_roles_menu', manage_roles_menu),
            ('edit_user_flow', start_edit_user_flow),
            ('edit_flow', edit_user_conversation_handler),
            ('edit_cancel', cancel_edit),#

            # Работа с отчетом
            #('report_menu', report_menu),
            ('creating_report', report_manager.process_cash_morning),
            ('adding_expense', report_manager.process_expense),
            ('adding_cash_in', report_manager.process_cash_in),
            ('adding_online', report_manager.process_online_cash),
        ]
        
        for key, handler in processes:
            if key in user_data:
                await handler(update, context)
                return True
        
        return False

    async def _handle_edit_user_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   text: str) -> bool:
        """Обработать процесс редактирования пользователя"""
        from handlers.admin_edit_user_flow import (
            select_user_for_edit, 
            enter_new_value,
            cancel_edit,
            EDIT_SELECT_USER, 
            EDIT_ENTER_VALUE
        )
        
        user_data = context.user_data
        state = user_data.get('edit_user_state')
        
        try:
            if state == EDIT_SELECT_USER:
                # Обрабатываем ввод ID пользователя
                await select_user_for_edit(update, context)
                return True
                
            elif state == EDIT_ENTER_VALUE:
                # Обрабатываем ввод нового значения
                await enter_new_value(update, context)
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обработки процесса редактирования пользователя: {e}")
            # Если ошибка - отменяем процесс
            await cancel_edit(update, context)
            user_data.clear()
        
        return False
    
    async def _handle_list_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     text: str) -> bool:
        """Обработать навигацию в списках"""
        user_data = context.user_data
        
        # Навигационные кнопки для общего списка клиентов
        if 'all_customers_list' in user_data:
            navigation_buttons = [
                Buttons.GET_MY_BONUS,
                Buttons.GET_MY_STAT,
                Buttons.BACK_TO_MAIN,
                Buttons.BACK_TO_CUSTOMERS
            ]
            
            if text in navigation_buttons:
                if text == Buttons.GET_MY_BONUS:
                    await self.handlers['show_my_bonuses'](update, context)
                elif text == Buttons.GET_MY_STAT:
                    await self.handlers['show_my_stat'](update, context)
                elif text == Buttons.BACK_TO_CUSTOMERS:
                    await self.handlers['customers_menu'](update, context)
                return True
                    
            else:
                await hand_cust_manager.handle_customer_selection(update, context)
                return True
        #await self._cleanup_context(context)
        # Навигационные кнопки для результатов поиска
        if 'search_results' in user_data:
            navigation_buttons = [
                Buttons.NEW_SEARCH,
                Buttons.BACK_TO_CUSTOMERS
            ]
            if text in navigation_buttons:
                if text == Buttons.NEW_SEARCH:
                    await self.handlers['search_customer'](update, context)
                elif text == Buttons.BACK_TO_CUSTOMERS:
                    await self.handlers['customers_menu'](update, context)
                return True
            else:
                await hand_cust_manager.handle_customer_selection(update, context)
                return True
        
        return False
    
    def cleanup_context(context):
        """Статический метод для очистки контекста"""
        keys_to_remove = ['all_customers_list', 'search_results', 'searching_customer']
        for key in keys_to_remove:
            context.user_data.pop(key, None)

    async def _cleanup_context(self, context: ContextTypes.DEFAULT_TYPE):
        """Алиас для обратной совместимости"""
        self.cleanup_context(context)
    
    async def _show_main_menu(self, user_id: int):
        """Показать главное меню"""
        await get_main_keyboard(user_id)

# Фабрика для создания обработчика
def create_message_handler(handlers_registry: dict):
    """Создать экземпляр обработчика сообщений"""
    handler = MessageHandler(handlers_registry)
    return handler.handle_message