"""
Конфигурация структуры меню и разрешений
"""

from handlers.admin_roles_class import Permission, UserRole
from config.buttons import Buttons

class MenuConfig:
    """Конфигурация меню и их разрешений"""
    
    # Главное меню и его пункты
    MAIN_MENU = {
        Buttons.INVENTORY: Permission.VIEW_INVENTORY,
        Buttons.REMINDERS: Permission.VIEW_REMINDERS,
        Buttons.CUSTOMERS: {
            'role': UserRole.VISITOR,
            'invert': True  # Доступно всем, кроме VISITOR
        },
        Buttons.GET_MY_STAT: {
            'role': UserRole.VISITOR,
            'invert': False
        },
        Buttons.GET_MY_BONUS: {
            'role': UserRole.VISITOR,
            'invert': False
        },
        Buttons.BONUS_SYSTEM: Permission.VIEW_BONUSES,
        Buttons.ADMINISTRATION: UserRole.ADMIN,  # Только админам
        Buttons.TOOLS: None,
        Buttons.PROFILE: None,  # Доступно всем
        Buttons.REPORT: Permission.VIEW_REPORTS,
        Buttons.EXIT: None
    }
    
    # Подменю инвентаризации
    INVENTORY_SUBMENU = {
        Buttons.INVENTORY_LIST: None,  # Все могут видеть
        Buttons.ADD_ITEM: Permission.MANAGE_INVENTORY,
        Buttons.COMPARE_INVENTORY: Permission.MANAGE_INVENTORY,
        Buttons.CLEAR_INVENTORY: Permission.MANAGE_INVENTORY,
        Buttons.CATALOG: Permission.MANAGE_INVENTORY,
        Buttons.VIEW_CATALOG: Permission.MANAGE_INVENTORY,
        Buttons.CREATE_LIST: Permission.MANAGE_INVENTORY,
        Buttons.CONFIRM_INVENTORY: Permission.CONFIRM_INVENTORY,
        Buttons.BACK_TO_MAIN: None
    }
    
    # Подменю напоминаний
    REMINDERS_SUBMENU = {
        Buttons.REMINDERS_STATUS: None,  # Все могут видеть статус
        Buttons.SETUP_SCHEDULE: Permission.MANAGE_REMINDERS,
        Buttons.SETUP_TYPE: Permission.MANAGE_REMINDERS,
        Buttons.START_REMINDERS: Permission.MANAGE_REMINDERS,
        Buttons.STOP_REMINDERS: Permission.MANAGE_REMINDERS,
        Buttons.CHECK_JOBS: Permission.MANAGE_REMINDERS,
        Buttons.RELOAD_JOBS: Permission.MANAGE_REMINDERS,
        Buttons.BACK_TO_MAIN: None
    }
    
    # Подменю клиентов
    CUSTOMERS_SUBMENU = {
        Buttons.REGISTER_CUSTOMER: {
            'role': UserRole.VISITOR,
            'invert': True
        },
        Buttons.CUSTOMERS_LIST: {
            'role': UserRole.VISITOR,
            'invert': True
        },
        Buttons.SEARCH_CUSTOMER: {
            'role': UserRole.VISITOR,
            'invert': True
        },
        Buttons.ADD_PURCHASE: {
            'role': UserRole.MANAGER,
            'invert': True
        },
        Buttons.ACTIVATE_CUSTOMER: {
            'role': UserRole.MANAGER,
            'invert': True
        },
        Buttons.DEACTIVATE_CUSTOMER: {
            'role': UserRole.MANAGER,
            'invert': True
        },
        Buttons.CUSTOMER_STATISTICS: {
            'role': UserRole.MANAGER,
            'invert': True
        },
        Buttons.CHECK_STATUS: {
            'role': UserRole.MANAGER,
            'invert': True
        },
        Buttons.BACK_TO_MAIN: None
    }
    
    # Подменю бонусной системы
    BONUS_SUBMENU = {
        Buttons.LOYALTY_PROGRAM: Permission.MANAGE_BONUSES,
        Buttons.LEVELS_SETTINGS: Permission.MANAGE_BONUSES,
        Buttons.PROGRAMS_MANAGEMENT: Permission.MANAGE_BONUSES,
        Buttons.ADD_CUSTOMER_BONUS: Permission.MANAGE_BONUSES,
        Buttons.DEL_CUSTOMER_BONUS: Permission.MANAGE_BONUSES,
        Buttons.PROMOCODES: Permission.MANAGE_BONUSES,
        Buttons.BACK_TO_MAIN: None
    }
    
    # Подменю администрирования
    ADMIN_SUBMENU = {
        Buttons.USER_MANAGEMENT: UserRole.ADMIN,
        Buttons.ROLE_MANAGEMENT: UserRole.ADMIN,
        Buttons.SYSTEM_SETTINGS: UserRole.ADMIN,
        Buttons.SYSTEM_STATS: UserRole.ADMIN,
        Buttons.ALL_USERS: UserRole.ADMIN,
        Buttons.ALL_ROLS: UserRole.ADMIN,
        Buttons.ADD_USER: UserRole.ADMIN,
        Buttons.CREATE_ROLS: UserRole.ADMIN,
        Buttons.EDIT_ROLS: UserRole.ADMIN,
        Buttons.EDIT_USER: UserRole.ADMIN,
        Buttons.DELL_USER: UserRole.ADMIN,
        Buttons.BACK_TO_MAIN: None
    }
    
    # Подменю управления чатом
    CHAT_SUBMENU = {
        Buttons.CLEANUP_ALL: {
            'role': UserRole.ADMIN,
            'permission': Permission.CLEANUP_CHAT
        },
        Buttons.CLEANUP_OWN: Permission.CLEANUP_CHAT,
        Buttons.CLEANUP_COUNT: {
            'role': UserRole.ADMIN,
            'permission': Permission.CLEANUP_CHAT
        },
        Buttons.BACK_TO_CHAT: None
    }
    
    # Кнопки возврата между уровнями
    BACK_BUTTONS = {
        Buttons.BACK_TO_MAIN: None,
        Buttons.BACK_TO_CUSTOMERS: {
            'role': UserRole.VISITOR,
            'invert': True
        },
        Buttons.BACK_TO_BONUS: Permission.VIEW_BONUSES,
        Buttons.BACK_TO_ADMIN: UserRole.ADMIN,
        Buttons.BACK_TO_SETTINGS: UserRole.ADMIN
    }