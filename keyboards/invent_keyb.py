from telegram import ReplyKeyboardMarkup
from config.buttons import Buttons
from handlers.admin_roles_class import role_manager, Permission, UserRole

async def get_inventory_keyboard(user_id: int):
    """Клавиатура инвентаризации в зависимости от роли"""
    keyboard = []
    
    # Все могут видеть список
    keyboard.append([Buttons.INVENTORY_LIST])
    keyboard.append([Buttons.ADD_ITEM])
    keyboard.append([Buttons.CATALOG])
                     
    # Управление товарами
    if await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        keyboard.append([Buttons.CREATE_LIST, Buttons.COMPARE_INVENTORY])
        keyboard.append([Buttons.CLEAR_INVENTORY])
    
    # Подтверждение инвентаризации
    if await role_manager.has_permission(user_id, Permission.CONFIRM_INVENTORY):
        keyboard.append([Buttons.CONFIRM_INVENTORY])
    
    # Назад
    keyboard.append([Buttons.BACK_TO_MAIN])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_units_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["шт", "кг", "г", "л"],
            ["мл", "упак", "банка", "бутылка"],
            ["пачка", "❌ Отмена"]
        ],
        resize_keyboard=True
    )

async def get_catalog_keyboard(user_id: int = None):
    """Меню управления справочником товаров"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ADD_CATALOG, Buttons.VIEW_CATALOG],
            [Buttons.EDIT_CATALOG, Buttons.EDIT_CATEGORY, Buttons.DEL_ITEM_CATALOG],
            [Buttons.BACK_TO_INVENTORY]
        ],
        resize_keyboard=True
    )

async def get_categories_keyboard(categories: list = None):
    """Клавиатура с категориями товаров"""
    keyboard = []
    
    if categories:
        for category in categories:
            category_name = category['category'] if isinstance(category, dict) else category
            keyboard.append([f"📁 {category_name}"])
    
    keyboard.append([Buttons.BACK_TO_CATALOG])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def get_products_by_category_keyboard(products: list):
    """Клавиатура с товарами категории"""
    keyboard = []
    
    for product in products:
        product_name = product['name'] if isinstance(product, dict) else product
        product_id = product['product_id'] if isinstance(product, dict) else "N/A"
        
        btn_text = f"🏷️ {product_id}: {product_name[:20]}"
        if len(btn_text) > 30:
            btn_text = f"🏷️ {product_id}: {product_name[:15]}..."
        keyboard.append([btn_text])
    
    keyboard.append([Buttons.OTHER_CATEGORY, Buttons.ADD_CATALOG])
    keyboard.append([Buttons.BACK_TO_CATALOG])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)