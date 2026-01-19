
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from enum import Enum
from config.buttons import Buttons
from handlers.admin_roles_class import role_manager, Permission, UserRole


class EditUserStep(Enum):
    SELECT_USER = "select_user"
    SELECT_FIELD = "select_field"
    ENTER_VALUE = "enter_value"
    CONFIRM = "confirm"

    def get_edit_user_field_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для выбора поля для редактирования"""
        keyboard = [
            [InlineKeyboardButton("👤 Username", callback_data=f"edit_user_field_{user_id}_username")],
            [InlineKeyboardButton("📛 First Name", callback_data=f"edit_user_field_{user_id}_first_name")],
            [InlineKeyboardButton("📛 Last Name", callback_data=f"edit_user_field_{user_id}_last_name")],
            [InlineKeyboardButton("📱 Phone Number", callback_data=f"edit_user_field_{user_id}_phone_numb")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_user_management")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_edit_user_confirm_keyboard(user_id: int, field: str, value: str) -> InlineKeyboardMarkup:
        """Клавиатура для подтверждения редактирования"""
        keyboard = [
            [InlineKeyboardButton(Buttons.EDIT_USER_CONFIRM, callback_data=f"edit_user_confirm_{user_id}_{field}_{value}")],
            [InlineKeyboardButton(Buttons.EDIT_USER_CANCEL, callback_data="edit_user_cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)

async def get_admin_keyboard():
    """Главное меню администрирования"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.USER_MANAGEMENT, Buttons.ROLE_MANAGEMENT],
            [Buttons.SYSTEM_SETTINGS, Buttons.SYSTEM_STATS],
            [Buttons.BACK_TO_MAIN]
        ],
        resize_keyboard=True
    )

async def get_user_management_keyboard():
    """Меню управления пользователями"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ALL_USERS, Buttons.EDIT_USER],
            [Buttons.ADD_USER, Buttons.DELL_USER],
            [Buttons.BACK_TO_ADMIN]
        ],
        resize_keyboard=True
    )

async def get_role_management_keyboard():
    """Меню управления ролями"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ALL_ROLS, Buttons.SET_ROLS],
            [Buttons.CREATE_ROLS, Buttons.EDIT_ROLS],
            [Buttons.BACK_TO_ADMIN]
        ],
        resize_keyboard=True
    )

async def get_profile_keyboard(user_id: int):
    """Клавиатура профиля"""
    keyboard = []
    
    role = await role_manager.get_user_role(user_id)
    
    # Информация о профиле доступна всем
    keyboard.append([Buttons.PROFILE_INFO])
    
    # Смена роли только для админов (для себя)
    if role == UserRole.ADMIN:
        keyboard.append([Buttons.CHANGE_ROLE])
    
    keyboard.append([Buttons.BACK_TO_MAIN])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def get_system_settings_keyboard():
    """Меню общих настроек"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.FEATURES_MANAGEMENT, Buttons.CHAT_MANAGEMENT],
            [Buttons.BOT_SETTINGS, Buttons.NOTIFICATIONS],
            [Buttons.BACK_TO_ADMIN]
        ],
        resize_keyboard=True
    )

async def get_features_management_keyboard():
    """Меню управления функциями системы"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ACTIVATE_FUNC, Buttons.DEACIVEATE_FUNC],
            [Buttons.STATS_FUNC],
            [Buttons.BACK_TO_SETTINGS]
        ],
        resize_keyboard=True
    )

async def get_chat_management_keyboard(user_id: int):
    """Клавиатура управления чатом в зависимости от роли"""
    keyboard = []
    
    role = await role_manager.get_user_role(user_id)

    if await role_manager.has_permission(user_id, Permission.CLEANUP_CHAT):
        keyboard.append([Buttons.CLEANUP_OWN])
       
        if role == UserRole.ADMIN:
            keyboard.append([Buttons.CLEANUP_ALL, Buttons.CLEANUP_COUNT])

    keyboard.append([Buttons.BACK_TO_CHAT])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)