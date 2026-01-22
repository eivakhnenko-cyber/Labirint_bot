from telegram import ReplyKeyboardMarkup
from handlers.admin_roles_class import role_manager, Permission, UserRole
from config.buttons import Buttons

async def get_main_keyboard(user_id: int = None):
    """Главная клавиатура в зависимости от роли"""
    if user_id is None:
        # Дефолтная клавиатура для незарегистрированных
        keyboard = [
            [[Buttons.PROFILE]]
        ]
    else:
        keyboard = []
        # Проверяем разрешения
        has_inventory = await role_manager.has_permission(user_id, Permission.VIEW_INVENTORY)
        has_reminders = await role_manager.has_permission(user_id, Permission.VIEW_REMINDERS)
        has_bonuses = await role_manager.has_permission(user_id, Permission.VIEW_BONUSES)
       # has_chat = await role_manager.has_permission(user_id, Permission.CLEANUP_CHAT)
        has_reports = await role_manager.has_permission(user_id, Permission.VIEW_REPORTS)

        role = await role_manager.get_user_role(user_id)
        
        # Администрирование (только для админов)
        if role == UserRole.ADMIN or UserRole.MANAGER:
            keyboard.append([Buttons.ADMINISTRATION, Buttons.BONUS_SYSTEM]) 
        keyboard.append([Buttons.REPORT, Buttons.TOOLS])
        # Клиенты (доступно для всех, кроме посетителей)
        if role != UserRole.GUEST:
            keyboard.append([Buttons.CUSTOMERS])
        # Профиль
        keyboard.append([Buttons.PROFILE])

        # Выход
        keyboard.append([Buttons.EXIT])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_tools_keyboard():
    return ReplyKeyboardMarkup(
        [
        [Buttons.INVENTORY, Buttons.REMINDERS],
        [Buttons.BACK_TO_MAIN]
        ],
        resize_keyboard=True
    )


def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        [[Buttons.CANCEL]],
        resize_keyboard=True
    )


def get_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        [[Buttons.CONFIRM_DEL_YES, Buttons.CONFIRM_DEL_NO]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_back_keyboard():
    return ReplyKeyboardMarkup([[Buttons.BACK_TO_MAIN]], resize_keyboard=True)