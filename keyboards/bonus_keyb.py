
from telegram import ReplyKeyboardMarkup
from config.buttons import Buttons
from handlers.admin_roles_class import role_manager, Permission, UserRole


async def get_bonus_system_keyboard(user_id: int):
    """Главное меню бонусной системы"""
    keyboard = []
    
    role = await role_manager.get_user_role(user_id)
    
    
    if role == UserRole.ADMIN:    
        keyboard.append([Buttons.LOYALTY_PROGRAM, Buttons.LEVELS_SETTINGS])
        keyboard.append([Buttons.PROMOCODES])
    
    elif role == UserRole.MANAGER:
        keyboard.append([Buttons.SEARCH_CUSTOMER, Buttons.CUSTOMER_STATISTICS])
        keyboard.append([Buttons.ADD_CUSTOMER_BONUS, Buttons.DEL_CUSTOMER_BONUS])

    elif role == UserRole.VISITOR:
        keyboard.append([Buttons.GET_MY_BONUS, Buttons.GET_MY_STAT])
        keyboard.append([Buttons.GET_MY_LEVEL])
    
    elif role == UserRole.GUEST:
        keyboard.append([Buttons.EXIT])
        

    keyboard.append([Buttons.BACK_TO_MAIN])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    

async def get_loyalty_program_keyboard():
    """Меню программы лояльности"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ADD_PROGRAM, Buttons.LIST_PROGRAM],
            [Buttons.ANALITIC_PROGRAM, Buttons.SEARCH_PROGRAM],
            [Buttons.BACK_TO_BONUS]
        ],
        resize_keyboard=True
    )

async def get_levels_management_keyboard():
    """Меню настройки уровней"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ADD_LEVELS, Buttons.LIST_LEVELS],
            [Buttons.EDIT_LEVEL, Buttons.DELETE_LEVELS],
            [Buttons.STATICS_LEVELS],
            [Buttons.BACK_TO_BONUS]
        ],
        resize_keyboard=True
    )

async def get_programs_management_keyboard():
    """Меню управления программами"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ACTIVATE_PROGRAM, Buttons.DEACIVATE_PROGRAM],
            [Buttons.BACK_TO_BONUS]
        ],
        resize_keyboard=True
    )

async def get_promocodes_keyboard():
    """Меню промокодов"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.PROMO_LIST, Buttons.PROMO_ADD],
            [Buttons.PROMO_ACTIVATE, Buttons.PROMO_STAT],
            [Buttons.BACK_TO_BONUS]
        ],
        resize_keyboard=True
    )

async def get_bonus_keyboard(user_id: int):
    """Клавиатура бонусной системы"""
    keyboard = []
    
    role = await role_manager.get_user_role(user_id)

    # Просмотр бонусов доступен всем
    if role == UserRole.VISITOR:
        keyboard.append([Buttons.GET_MY_BONUS, Buttons.GET_MY_STAT])
    elif role == UserRole.GUEST:
        keyboard.append([Buttons.PROFILE_INFO])

    # Управление бонусами
    if await role_manager.has_permission(user_id, Permission.MANAGE_BONUSES):
        keyboard.append([Buttons.ADD_CUSTOMER_BONUS, Buttons.DEL_CUSTOMER_BONUS])

    if role == UserRole.ADMIN:
        keyboard.append([Buttons.LOYALTY_PROGRAM])
    
    keyboard.append([Buttons.BACK_TO_MAIN])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_confirm_bonus_keyboard():
    return ReplyKeyboardMarkup(
        [[Buttons.CONFIRM_YES, Buttons.CONFIRM_NO]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
def get_confirm_delete_levels_keyboard():
    """Клавиатура для подтверждения удаления"""
    
    keyboard = [
        [Buttons.CONFIRM_DEL_LEV_YES, Buttons.CONFIRM_DEL_LEV_NO]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)