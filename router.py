"""
Система маршрутизации для обработки текстовых сообщений
"""

import logging
from typing import Dict, Any, Callable, Optional, Awaitable
from telegram import Update
from telegram.ext import ContextTypes

from handlers.admin_roles_class import role_manager, Permission, UserRole
from config.buttons import Buttons
from config.permission_menus import MenuConfig

logger = logging.getLogger(__name__)

class Router:
    """Маршрутизатор для обработки кнопок меню"""
    
    def __init__(self):
        self.routes: Dict[str, Dict[str, Any]] = {}
        self._setup_routes()
    
    def _setup_routes(self):
        """Настройка всех маршрутов"""
        
        # Главное меню
        self._add_route(Buttons.INVENTORY, "inventory_menu")
        self._add_route(Buttons.REMINDERS, "reminders_menu")
        self._add_route(Buttons.CUSTOMERS, "customers_menu")
        self._add_route(Buttons.BONUS_SYSTEM, "bonus_menu")
        self._add_route(Buttons.ADMINISTRATION, "admin_menu")
        self._add_route(Buttons.PROFILE, "profile_menu")
        self._add_route(Buttons.REPORT, "report_menu")
        self._add_route(Buttons.EXIT, "exit_command")
        
        # Подменю инвентаризации (старая структура для обратной совместимости)
        self._add_route(Buttons.INVENTORY_LIST, "show_inventory")
        self._add_route(Buttons.ADD_ITEM, "add_item")
        self._add_route(Buttons.CREATE_LIST, "create_list")
        self._add_route(Buttons.COMPARE_INVENTORY, "compare_inventory")
        self._add_route(Buttons.CLEAR_INVENTORY, "clear_inventory")
        self._add_route(Buttons.CONFIRM_INVENTORY, "confirm_inventory")

        # Кнопки для работы со справочником (каталогом)
        self._add_route(Buttons.CATALOG, "manage_catalog")
        self._add_route(Buttons.ADD_CATALOG, "add_to_catalog")
        self._add_route(Buttons.EDIT_CATALOG, "edit_catalog_item")
        self._add_route(Buttons.VIEW_CATALOG, "browse_catalog")
        self._add_route(Buttons.EDIT_CATEGORY, "edit_catalog_category")
        self._add_route(Buttons.DEL_ITEM_CATALOG, "del_item_catalog")
        self._add_route(Buttons.SELECT_CATALOG, "selecting_from_catalog")
        self._add_route(Buttons.ADD_ARM_CATALOG, "add_to_catalog")
        
        # Подменю напоминаний (старая структура)
        self._add_route(Buttons.REMINDERS_STATUS, "show_reminders_status")
        self._add_route(Buttons.SETUP_SCHEDULE, "setup_schedule")
        self._add_route(Buttons.SETUP_TYPE, "setup_reminder_type")
        self._add_route(Buttons.START_REMINDERS, "start_reminders")
        self._add_route(Buttons.STOP_REMINDERS, "stop_reminders")
        self._add_route(Buttons.CHECK_JOBS, "check_jobs")
        self._add_route(Buttons.RELOAD_JOBS, "reload_reminders")
        
        # Подменю управления чатом
        self._add_route(Buttons.CLEANUP_CHAT, "cleanup_menu")
        self._add_route(Buttons.CLEANUP_ALL, "cleanup_all_messages")
        self._add_route(Buttons.CLEANUP_OWN, "cleanup_own_messages")
        self._add_route(Buttons.CLEANUP_COUNT, "request_message_count")
        
        # ========== БОНУСНАЯ СИСТЕМА - ГЛАВНОЕ ==========
        self._add_route(Buttons.LOYALTY_PROGRAM, "loyalty_program_menu")
        self._add_route(Buttons.LEVELS_SETTINGS, "levels_settings_menu")
        self._add_route(Buttons.PROGRAMS_MANAGEMENT, "programs_management_menu")
        self._add_route(Buttons.PROMOCODES, "promocodes_menu")
        
        # ========== ПРОГРАММА ЛОЯЛЬНОСТИ ==========
        self._add_route(Buttons.ADD_PROGRAM, "create_program_handler")
        self._add_route(Buttons.LIST_PROGRAM, "list_programs_handler")
        self._add_route(Buttons.ANALITIC_PROGRAM, "program_statistics_handler")
        self._add_route(Buttons.SEARCH_PROGRAM, "search_program_handler")
        self._add_route(Buttons.ADD_LEVELS, "create_level_handler") 
        self._add_route(Buttons.LIST_LEVELS, "list_levels_handler")  
        self._add_route(Buttons.EDIT_LEVEL, "edit_level_handler") 
        self._add_route(Buttons.STATICS_LEVELS, "level_statistics_handler")
        self._add_route(Buttons.DELETE_LEVELS, "delete_level_handler")

        # Подменю администрирования
        self._add_route(Buttons.USER_MANAGEMENT, "manage_users_menu")
        self._add_route(Buttons.ROLE_MANAGEMENT, "manage_roles_menu")
        self._add_route(Buttons.SYSTEM_SETTINGS, "system_settings_menu")
        self._add_route(Buttons.SYSTEM_STATS, "system_stats")
        self._add_route(Buttons.FEATURES_MANAGEMENT, "features_management_menu")
        self._add_route(Buttons.CHAT_MANAGEMENT, "chat_management_menu")
        self._add_route(Buttons.BOT_SETTINGS, "bot_settings_menu")
        self._add_route(Buttons.NOTIFICATIONS, "notifications_menu")

        # пользователи ситсемы
        self._add_route(Buttons.ALL_USERS, "get_all_users")
        self._add_route(Buttons.ADD_USER, "add_user")
        self._add_route(Buttons.EDIT_USER, "edit_user")
        self._add_route(Buttons.DELL_USER, "del_user")


        # управление ролями
        self._add_route(Buttons.ALL_ROLS, "get_all_rols")
        self._add_route(Buttons.CREATE_ROLS, "add_rols")
        self._add_route(Buttons.EDIT_ROLS, "edit_rols")

        
        # Подменю клиентов
        self._add_route(Buttons.REGISTER_CUSTOMER, "register_customer_handler")
        self._add_route(Buttons.CUSTOMERS_LIST, "list_customers_handler")
        self._add_route(Buttons.SEARCH_CUSTOMER, "search_customer_menu_handler")
        self._add_route(Buttons.ADD_PURCHASE, "add_purchase_handler")
        self._add_route(Buttons.ACTIVATE_CUSTOMER, "activate_customer")
        self._add_route(Buttons.DEACTIVATE_CUSTOMER, "deactivate_customer")
        self._add_route(Buttons.CHECK_STATUS, "check_status_handler")
        self._add_route(Buttons.GET_MY_BONUS, "show_my_bonuses") #show_my_bonuses
        self._add_route(Buttons.GET_MY_LEVEL, "get_my_level")
        self._add_route(Buttons.GET_MY_STAT, "show_my_stat")

        # Поиск клиента
        self._add_route(Buttons.SEARCH_BY_CARD, "search_by_card")
        self._add_route(Buttons.SEARCH_BY_PHONE, "search_by_phone")
        self._add_route(Buttons.SEARCH_BY_NAME, "search_by_name")
        self._add_route(Buttons.SEARCH_BY_ID, "search_by_id")
        self._add_route(Buttons.PURCHASE_HISTORY, "purchase_history")
        self._add_route(Buttons.NEW_SEARCH, "search_customer")
        
        # Кнопки возврата
        self._add_route(Buttons.BACK, "back_to_main")
        self._add_route(Buttons.BACK_TO_MAIN, "back_to_main")
        self._add_route(Buttons.BACK_TO_CUSTOMERS, "back_to_customers")
        self._add_route(Buttons.BACK_TO_BONUS, "back_to_bonus")
        self._add_route(Buttons.BACK_TO_ADMIN, "back_to_admin")
        self._add_route(Buttons.BACK_TO_SETTINGS, "back_to_settings")
        self._add_route(Buttons.BACK_TO_CHAT, "back_to_chat")
        
        # Профиль
        self._add_route(Buttons.PROFILE_INFO, "profile_info")
        self._add_route(Buttons.ALL_USERS, "get_all_users")
        self._add_route(Buttons.CHANGE_ROLE, "set_user_role_command")

        # Меню отчетов
        self._add_route(Buttons.START_WATCH, "start_report")
        self._add_route(Buttons.STOP_WATCH, "stop_watch")
        self._add_route(Buttons.REPORT_HISTORY, "report_history")
    
    def _add_route(self, button_text: str, handler_name: str):
        """Добавить маршрут для кнопки"""
        self.routes[button_text] = {
            'handler': handler_name,
            'config': self._get_menu_config(button_text)
        }
    
    def _get_menu_config(self, button_text: str) -> Optional[Dict[str, Any]]:
        """Получить конфигурацию для кнопки из MenuConfig"""
        # Проверяем все категории меню
        menus = [
            MenuConfig.MAIN_MENU,
            MenuConfig.INVENTORY_SUBMENU,
            MenuConfig.REMINDERS_SUBMENU,
            MenuConfig.CUSTOMERS_SUBMENU,
            MenuConfig.BONUS_SUBMENU,
            MenuConfig.ADMIN_SUBMENU,
            MenuConfig.CHAT_SUBMENU,
            MenuConfig.BACK_BUTTONS
        ]
        
        for menu in menus:
            if button_text in menu:
                return menu[button_text]
        
        return None
    
    async def check_permission(self, user_id: int, button_text: str) -> bool:
        """Проверить права доступа для кнопки"""
        config = self.routes.get(button_text, {}).get('config')
        
        if config is None:
            return True  # Нет ограничений
        
        # Если конфиг - это Permission
        if isinstance(config, Permission):
            return await role_manager.has_permission(user_id, config)
        
        # Если конфиг - это UserRole (только для определенной роли)
        if isinstance(config, UserRole):
            user_role = await role_manager.get_user_role(user_id)
            return user_role == config
        
        # Если конфиг - это словарь
        if isinstance(config, dict):
            if 'role' in config:
                user_role = await role_manager.get_user_role(user_id)
                invert = config.get('invert', False)
                
                if invert:
                    return user_role != config['role']
                else:
                    return user_role == config['role']
            
            if 'permission' in config:
                has_permission = await role_manager.has_permission(user_id, config['permission'])
                if 'role' in config:
                    user_role = await role_manager.get_user_role(user_id)
                    return has_permission and user_role == config['role']
                return has_permission
        
        return False
    
    async def route(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                   button_text: str) -> Optional[str]:
        """Перенаправить на соответствующий обработчик"""
        if button_text not in self.routes:
            return None
        
        user_id = update.effective_user.id
        
        # Проверяем права доступа
        if not await self.check_permission(user_id, button_text):
            await update.message.reply_text("❌ Нет доступа к этой функции")
            return "access_denied"
        
        return self.routes[button_text]['handler']
    
    def get_all_routes(self) -> Dict[str, str]:
        """Получить все зарегистрированные маршруты"""
        return {text: data['handler'] for text, data in self.routes.items()}


# Глобальный экземпляр роутера
router = Router()