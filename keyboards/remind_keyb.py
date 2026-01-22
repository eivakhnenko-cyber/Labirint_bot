from telegram import ReplyKeyboardMarkup
from config.buttons import Buttons
from handlers.admin_roles_class import role_manager, Permission, UserRole


async def get_reminders_keyboard(user_id: int):
    """Клавиатура напоминаний в зависимости от роли"""
    keyboard = []
    
    # Просмотр статуса
    keyboard.append([Buttons.REMINDERS_STATUS])
    
    # Управление напоминаниями
    if await role_manager.has_permission(user_id, Permission.MANAGE_REMINDERS):
        keyboard.append([Buttons.SETUP_SCHEDULE, Buttons.SETUP_TYPE])
        keyboard.append([Buttons.START_REMINDERS, Buttons.STOP_REMINDERS])
        keyboard.append([Buttons.CHECK_JOBS, Buttons.RELOAD_JOBS])
    
    # Назад
    keyboard.append([Buttons.BACK])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def get_reminder_type_keyboard(user_id: int = None):
    """Клавиатура для выбора типа напоминания"""
    return ReplyKeyboardMarkup(
    [
        [Buttons.CHECK_REST],
        [Buttons.START_INVENT],
        [Buttons.OWN_VERSION],
        [Buttons.BACK_TO_REMIND]
    ],
     resize_keyboard=True, one_time_keyboard=True
    )

def get_schedule_day_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Пн", "Вт", "Ср"],
            ["Чт", "Пт", "Сб"],
            ["Вс", Buttons.BACK]
        ],
        resize_keyboard=True
    )