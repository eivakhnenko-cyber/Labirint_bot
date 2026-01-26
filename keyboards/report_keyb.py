from telegram import ReplyKeyboardMarkup
from handlers.admin_roles_class import role_manager, UserRole
from config.buttons import Buttons

async def get_main_report_keyboard(user_id: int = None):
    """Главная отчеты"""
    keyboard = [] 

    # role = role_manager.get_user_role(user_id)  
    # if role == UserRole.BARISTA:
    # Управление отчетами
    keyboard.append([Buttons.START_WATCH, Buttons.STOP_WATCH])
    keyboard.append([Buttons.REPORT_HISTORY])
    
    # Назад
    keyboard.append([Buttons.BACK_TO_MAIN])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)