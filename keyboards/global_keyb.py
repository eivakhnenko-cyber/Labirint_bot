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
      
        # Администрирование (только для админов)
        keyboard.append([Buttons.ADMINISTRATION, Buttons.BONUS_SYSTEM]) 
        keyboard.append([Buttons.REPORT, Buttons.TOOLS])
        # Клиенты (доступно для всех, кроме посетителей)
        keyboard.append([Buttons.CUSTOMERS, Buttons.PROFILE])
        # Профиль
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