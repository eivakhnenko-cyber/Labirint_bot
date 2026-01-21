import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from database import sqlite_connection
from config.buttons import Buttons
from handlers.admin_roles_class import role_manager, Permission, UserRole
from keyboards.global_keyb import get_cancel_keyboard, get_main_keyboard
from keyboards.invent_keyb import get_catalog_keyboard, get_categories_keyboard, get_inventory_keyboard
from handlers.catalog_cervices_class import CatalogRepository
from utils.telegram_utils import send_or_edit_message

logger = logging.getLogger(__name__)

# Callback data prefixes
CATEGORY_BROWSE_PREFIX = "browse_cat_"
CATEGORY_SELECT_PREFIX = "select_cat_"
CATEGORY_DELETE_PREFIX = "delete_cat_"
PRODUCT_VIEW_PREFIX = "view_prod_"
PRODUCT_SELECT_PREFIX = "select_prod_"
EDIT_CATEGORY_PREFIX = "edit_cat_"
EDIT_PRODUCT_PREFIX = "edit_prod_"
EDIT_FIELD_PREFIX = "edit_field_"
CONFIRM_DELETE_SINGLE = "confirm_del_single_"
CONFIRM_DELETE_ALL = "confirm_del_all_"
SAVE_EDIT_PREFIX = "save_edit_"


async def manage_catalog(update: Update, context: CallbackContext) -> None:
    """Управление справочником товаров"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await send_or_edit_message(
            update=update,
            text="❌ У вас нет прав для управления справочником товаров.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    await send_or_edit_message(
        update=update,
        text="📋 *Управление справочником товаров*\n\nВыберите действие:",
        reply_markup=await get_catalog_keyboard(user_id),
        parse_mode='Markdown'
    )

async def add_to_catalog(update: Update, context: CallbackContext) -> None:
    """Добавление товара в справочник"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await send_or_edit_message(
            update=update,
            text="❌ У вас нет прав для добавления товаров в справочник.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    context.user_data['adding_to_catalog'] = {
        'step': 'category',
        'data': {}
    }
    
    # Получаем существующие категории для подсказки
    categories = CatalogRepository.get_active_categories()
    
    categories_text = ""
    if categories:
        categories_text = "\n\n📁 *Существующие категории:*\n" + "\n".join([f"• {cat}" for cat in categories])
    
    await send_or_edit_message(
        update=update,
        text=f"➕ *Добавление товара в справочник*\n\nВведите категорию товара (например: 'Напитки', 'Выпечка', 'Десерты'):{categories_text}",
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown',
        delete_previous=True  # Важно! Удаляем inline-сообщение перед отправкой обычного
    )

async def del_item_catalog(update: Update, context: CallbackContext) -> None:
    """Удаление товара из справочника с inline-кнопками для выбора категории"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await send_or_edit_message(
            update=update,
            text="❌ У вас нет прав для удаления товаров из справочника.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Получаем существующие категории для отображения
    categories = CatalogRepository.get_active_categories()
    
    if not categories:
        await send_or_edit_message(
            update=update,
            text="📭 Справочник товаров пуст. Нечего удалять.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    # Создаем inline-клавиатуру с категориями
    keyboard = []
    for category in categories:
        callback_data = f"{CATEGORY_DELETE_PREFIX}{category}"
        keyboard.append([InlineKeyboardButton(f"🗑️ {category}", callback_data=callback_data)])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_or_edit_message(
        update=update,
        text=(f"🗑️ *Удаление товара из справочника*\n\n",
        "*Выберите категорию товара для удаления:*"),
        reply_markup=reply_markup,
        parse_mode='Markdown',
        delete_previous=True  # Важно! Удаляем inline-сообщение перед отправкой обычного
    )

async def process_catalog_deletion(update: Update, context: CallbackContext) -> None:
    """Обработка удаления товара из справочника - для текстовых сообщений"""
    
    if 'deleting_from_catalog' not in context.user_data:
        return
    
    text = update.message.text.strip()
    process = context.user_data['deleting_from_catalog']
    step = process['step']
    user_id = update.effective_user.id
    
    if text == Buttons.CANCEL:
        del context.user_data['deleting_from_catalog']
        await send_or_edit_message(
            update=update,
            text="❌ Удаление отменено.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    # Остальная логика остается без изменений...
    if step == 'category':
        if not text:
            await update.message.reply_text("Введите категорию товара:")
            return
        
        if not CatalogRepository.check_category_exists(text):
            await send_or_edit_message(
                update=update,
                text=(f"❌ В категории '{text}' нет активных товаров.\n"
                f"Введите другую категорию:"),
                reply_markup=get_cancel_keyboard()
            )
            return
        
        process['data']['category'] = text
        process['step'] = 'select_product'
        
        products = CatalogRepository.get_category_products(text)
        
        if not products:
            await send_or_edit_message(
                update=update,
                text=f"❌ В категории '{text}' нет товаров для удаления.",
                reply_markup=await get_catalog_keyboard(user_id)
            )
            del context.user_data['deleting_from_catalog']
            return
        
        process['data']['products'] = products
        
        # Формируем inline-клавиатуру для выбора товара
        keyboard = []
        for idx, product in enumerate(products, 1):
            product_text = f"{product['name']}"
            if len(product_text) > 30:
                product_text = f"{product['name'][:27]}..."
            callback_data = f"{PRODUCT_SELECT_PREFIX}{product['product_id']}"
            keyboard.append([InlineKeyboardButton(f"{idx}. {product_text}", callback_data=callback_data)])
        
        keyboard.append([
            InlineKeyboardButton("🗑️ Удалить ВСЕ товары категории", callback_data="delete_all_category"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"📋 *Товары в категории: {text}*\n\n"
        for idx, product in enumerate(products, 1):
            message += f"{idx}. 🏷️ *{product['name']}*\n"
            message += f"   📏 {product['unit']} | 🔢 {product['default_quantity']}\n"
            if product['description']:
                message += f"   📝 {product['description']}\n"
            message += f"   🆔 ID: {product['product_id']}\n\n"
        
        message += "*Или удалите все товары категории:*"
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif step == 'select_product':
        # Эта часть теперь обрабатывается через callback-запросы
        pass
    
    elif step == 'confirm_single':
        if text == "✅ Да, удалить":
            await delete_single_product(update, context, process['data'])
        else:
            del context.user_data['deleting_from_catalog']
            await send_or_edit_message(
                update=update,
                text="❌ Удаление отменено.",
                reply_markup=await get_catalog_keyboard(user_id)
            )
    
    elif step == 'confirm_all':
        if text == "✅ Да, удалить ВСЕ":
            await delete_all_category_products(update, context, process['data'])
        else:
            del context.user_data['deleting_from_catalog']
            await send_or_edit_message(
                update=update,
                text="❌ Удаление отменено.",
                reply_markup=await get_catalog_keyboard(user_id)
            )

async def delete_single_product(update: Update, context: CallbackContext, data: dict) -> None:
    """Удаление одного товара из справочника"""
    user_id = update.effective_user.id
    product = data['selected_product']
    
    success = CatalogRepository.soft_delete_product(product['product_id'])
    
    if success:
        del context.user_data['deleting_from_catalog']
        
        await update.message.reply_text(
            f"✅ *Товар успешно удален!*\n\n"
            f"🏷️ *Название:* {product['name']}\n"
            f"📁 *Категория:* {data['category']}\n"
            f"🆔 *ID товара:* {product['product_id']}\n\n"
            f"Товар помечен как неактивный и больше не будет отображаться в справочнике.",
            reply_markup=await get_catalog_keyboard(user_id),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка при удалении товара.",
            reply_markup=await get_catalog_keyboard(user_id)
        )

async def delete_all_category_products(update: Update, context: CallbackContext, data: dict) -> None:
    """Удаление всех товаров категории"""
    user_id = update.effective_user.id
    category = data['category']
    
    deleted_count = CatalogRepository.soft_delete_category_products(category)
    
    if deleted_count > 0:
        del context.user_data['deleting_from_catalog']
        
        await update.message.reply_text(
            f"✅ *Категория полностью очищена!*\n\n"
            f"📁 *Категория:* {category}\n"
            f"🗑️ *Удалено товаров:* {deleted_count}\n\n"
            f"Все товары помечены как неактивные и больше не будут отображаться в справочнике.",
            reply_markup=await get_catalog_keyboard(user_id),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка при удалении товаров категории.",
            reply_markup=await get_catalog_keyboard(user_id)
        )

async def process_catalog_addition(update: Update, context: CallbackContext) -> None:
    """Обработка добавления товара в справочник"""
    if 'adding_to_catalog' not in context.user_data:
        return
    
    text = update.message.text.strip()
    process = context.user_data['adding_to_catalog']
    step = process['step']
    user_id = update.effective_user.id
    
    if text == Buttons.CANCEL:
        del context.user_data['adding_to_catalog']
        await update.message.reply_text(
            "❌ Добавление отменено.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    # Вся логика добавления остается без изменений...
    if step == 'category':
        if not text:
            await update.message.reply_text("Введите категорию товара:")
            return
        
        process['data']['category'] = text
        process['step'] = 'name'
        
        await update.message.reply_text(
            "Введите название товара:",
            reply_markup=get_cancel_keyboard()
        )
    
    elif step == 'name':
        if not text:
            await update.message.reply_text("Введите название товара:")
            return
        
        if CatalogRepository.check_product_name_exists(text):
            await update.message.reply_text(
                "❌ Товар с таким названием уже существует.\n"
                "Введите другое название:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        process['data']['name'] = text
        process['step'] = 'unit'
        
        await update.message.reply_text(
            "Введите единицу измерения товара:\n"
            "Например: 'шт', 'кг', 'л', 'гр'",
            reply_markup=ReplyKeyboardMarkup(
                [["шт", "кг", "л", "гр", "мл", "❌ Отмена"]],
                resize_keyboard=True
            )
        )
    
    elif step == 'unit':
        process['data']['unit'] = text
        process['step'] = 'default_quantity'
        
        await update.message.reply_text(
            "Введите стандартное количество для этого товара:\n"
            "Например: 1, 0.5, 100",
            reply_markup=get_cancel_keyboard()
        )
    
    elif step == 'default_quantity':
        try:
            quantity = float(text)
            if quantity <= 0:
                await update.message.reply_text(
                    "Количество должно быть больше 0. Введите снова:",
                    reply_markup=get_cancel_keyboard()
                )
                return
            process['data']['default_quantity'] = quantity
            process['step'] = 'description'
            
            await update.message.reply_text(
                "Введите описание товара (необязательно):\n"
                "Или нажмите 'Пропустить'",
                reply_markup=ReplyKeyboardMarkup(
                    [["Пропустить", "❌ Отмена"]],
                    resize_keyboard=True
                )
            )
        except:
            await update.message.reply_text(
                "Введите корректное число:",
                reply_markup=get_cancel_keyboard()
            )
    
    elif step == 'description':
        if text == "Пропустить":
            process['data']['description'] = None
        else:
            process['data']['description'] = text
        
        process['step'] = 'confirm'
        
        confirm_text = (
            "✅ *Данные товара для справочника:*\n\n"
            f"📁 *Категория:* {process['data']['category']}\n"
            f"🏷️ *Название:* {process['data']['name']}\n"
            f"📏 *Единица измерения:* {process['data']['unit']}\n"
            f"🔢 *Стандартное количество:* {process['data']['default_quantity']}\n"
            f"📝 *Описание:* {process['data']['description'] or 'Не указано'}\n\n"
            "Добавить товар в справочник?"
        )
        
        await update.message.reply_text(
            confirm_text,
            reply_markup=ReplyKeyboardMarkup(
                [["✅ Да, добавить", "❌ Нет, отменить"]],
                resize_keyboard=True,
                one_time_keyboard=True
            ),
            parse_mode='Markdown'
        )
    
    elif step == 'confirm':
        if text == "✅ Да, добавить":
            await save_to_catalog(update, context, process['data'])
        else:
            del context.user_data['adding_to_catalog']
            await update.message.reply_text(
                "❌ Добавление отменено.",
                reply_markup=await get_catalog_keyboard(user_id)
            )

async def save_to_catalog(update: Update, context: CallbackContext, product_data: dict) -> None:
    """Сохранение товара в справочник"""
    user_id = update.effective_user.id
    
    product_id = CatalogRepository.add_product(
        category=product_data['category'],
        name=product_data['name'],
        unit=product_data['unit'],
        default_quantity=product_data['default_quantity'],
        description=product_data['description']
    )
    
    if product_id:
        del context.user_data['adding_to_catalog']
        
        await update.message.reply_text(
            f"✅ *Товар добавлен в справочник!*\n\n"
            f"🏷️ *Название:* {product_data['name']}\n"
            f"📁 *Категория:* {product_data['category']}\n"
            f"🆔 *ID товара:* {product_id}\n"
            f"📏 *Единица:* {product_data['unit']}\n"
            f"🔢 *Количество:* {product_data['default_quantity']}\n\n"
            f"Теперь этот товар можно выбирать при добавлении в инвентаризацию.",
            reply_markup=await get_catalog_keyboard(user_id),
            parse_mode='Markdown'
        )
    else:
        await send_or_edit_message(
            update=update,
            text="❌ Ошибка при добавлении товара в справочник.",
            reply_markup=await get_catalog_keyboard(user_id)
        )

async def browse_catalog(update: Update, context: CallbackContext) -> None:
    """Просмотр справочника товаров по категориям с inline-кнопками"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.VIEW_INVENTORY):
        await send_or_edit_message(
            update=update,
            text="❌ У вас нет прав для просмотра справочника товаров.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Получаем список категорий
    categories = CatalogRepository.get_all_categories_with_counts()
    
    if not categories:
        # Обработка для callback
        await send_or_edit_message(
            update=update,
            text="📭 Справочник товаров пуст.\nДобавьте товары через меню управления справочником.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    # Создаем inline-клавиатуру с категориями
    keyboard = []
    for category in categories:
        category_name = category['category']
        callback_data = f"{CATEGORY_BROWSE_PREFIX}{category_name}"
        keyboard.append([InlineKeyboardButton(
            f"📁 {category_name} ({category['count']} товаров)",
            callback_data=callback_data
        )])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Определяем способ отправки сообщения
    await send_or_edit_message(
        update=update,
        text="📋 *Справочник товаров*\n\n*Выберите категорию:*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_products_by_category(update: Update, context: CallbackContext, category: str = None) -> None:
    """Показать товары выбранной категории с inline-кнопками"""
    # Определяем источник вызова (callback или текстовое сообщение)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Извлекаем категорию из callback_data
        callback_data = query.data
        if callback_data.startswith(CATEGORY_BROWSE_PREFIX):
            category = callback_data[len(CATEGORY_BROWSE_PREFIX):]
        
        user_id = query.from_user.id
    else:
        text = update.message.text.strip()
        user_id = update.effective_user.id
        
        if text.startswith("📁 "):
            category = text[2:]  # Убираем эмодзи
        else:
            category = text
    
    if not category:
        await update.message.reply_text(
            "❌ Не указана категория.",
            reply_markup=await get_inventory_keyboard(user_id)
        )
        return
    
    logger.info(f"show_products_by_category: category='{category}'")
    
    products = CatalogRepository.get_category_products(category)
    
    if not products:
        # Создаем inline-клавиатуру для пустой категории
        keyboard = [
            [
                InlineKeyboardButton("📁 Другие категории", callback_data="other_categories"),
                InlineKeyboardButton("➕ Добавить товар", callback_data="add_product_catalog")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await query.edit_message_text(
                f"📭 В категории '{category}' нет товаров.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"📭 В категории '{category}' нет товаров.",
                reply_markup=reply_markup
            )
        return
    
    message = f"📋 *Товары категории: {category}*\n\n"
    
    # Создаем inline-клавиатуру с товарами
    keyboard = []
    for product in products:
        product_text = f"{product['name']} ({product['unit']})"
        if len(product_text) > 30:
            product_text = f"{product['name'][:25]}... ({product['unit']})"
        
        callback_data = f"{PRODUCT_VIEW_PREFIX}{product['product_id']}"
        keyboard.append([
            InlineKeyboardButton(f"🏷️ {product_text}", callback_data=callback_data)
        ])
        
        message += f"🏷️ *{product['name']}*\n"
        message += f"   📏 {product['unit']} | 🔢 {product['default_quantity']}\n"
        if product['description']:
            message += f"   📝 {product['description']}\n"
        message += f"   🆔 ID: {product['product_id']}\n\n"
    
    # Добавляем кнопки навигации
    keyboard.append([
        InlineKeyboardButton("📁 Другие категории", callback_data="other_categories"),
        InlineKeyboardButton("➕ Добавить товар", callback_data="add_product_catalog")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Сохраняем информацию для быстрого добавления
    context.user_data['selected_category'] = category
    context.user_data['catalog_products'] = products
    
    if update.callback_query:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def browse_catalog_for_selection(update: Update, context: CallbackContext) -> None:
    """Выбор товара из справочника для добавления в инвентаризацию с inline-кнопками"""
    user_id = update.effective_user.id
    
    # Получаем список категорий
    categories = CatalogRepository.get_active_categories()
    
    logger.info(f"Найдено категорий: {len(categories)}")
    
    if not categories:
        await update.message.reply_text(
            "📭 Справочник товаров пуст.\n"
            "Сначала добавьте товары в справочник или введите вручную.",
            reply_markup=ReplyKeyboardMarkup(
                [
                    [Buttons.ADD_ARM_CATALOG],
                    [Buttons.BACK_TO_INVENTORY]
                ],
                resize_keyboard=True
            )
        )
        return
    
    # Создаем inline-клавиатуру с категориями
    keyboard = []
    for cat_name in categories:
        logger.info(f"Категория: {cat_name}")
        callback_data = f"{CATEGORY_SELECT_PREFIX}{cat_name}"
        keyboard.append([InlineKeyboardButton(f"📁 {cat_name}", callback_data=callback_data)])
    
    # Добавляем кнопки навигации
    keyboard.append([
        InlineKeyboardButton("➕ Добавить товар", callback_data="add_product_catalog"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_inventory")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📋 *Выбор товара из справочника*\n\n"
        "*Выберите категорию:*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Устанавливаем флаг выбора из каталога
    context.user_data['selecting_from_catalog'] = True
    logger.info("Установлен флаг selecting_from_catalog")

async def edit_catalog_item(update: Update, context: CallbackContext) -> None:
    """Редактирование товара в справочнике"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await send_or_edit_message(
            update=update,
            text="❌ У вас нет прав для редактирования товаров в справочнике.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    context.user_data['editing_catalog'] = {
        'step': 'search',
        'data': {}
    }
    
    await send_or_edit_message(
        update=update,
        text=(f"✏️ *Редактирование товара в справочнике*\n\n"
        "Введите название товара или ID для поиска:"),
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown',
        delete_previous=True
    )

async def edit_catalog_category(update: Update, context: CallbackContext) -> None:
    """Изменение категории товаров с inline-кнопками"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await send_or_edit_message(
            update=update,
            text="❌ У вас нет прав для изменения категорий товаров.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    categories = CatalogRepository.get_active_categories()
    
    if not categories:
        await send_or_edit_message(
            update=update,
            text="📭 В справочнике нет активных категорий.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    context.user_data['editing_category'] = {
        'step': 'select_old',
        'data': {}
    }
    
    # Создаем inline-клавиатуру с категориями
    keyboard = []
    for category in categories:
        callback_data = f"{EDIT_CATEGORY_PREFIX}{category}"
        keyboard.append([InlineKeyboardButton(f"📁 {category}", callback_data=callback_data)])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit_category")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_or_edit_message(
        update=update,
        text=(f"🔄 *Изменение категории товаров*\n\n"
        "*Выберите категорию для изменения:*"),
        reply_markup=reply_markup,
        parse_mode='Markdown',
        delete_previous=True
    )

async def process_edit_catalog(update: Update, context: CallbackContext) -> None:
    """Обработка редактирования товара"""
    if 'editing_catalog' not in context.user_data:
        return
    
    text = update.message.text.strip()
    process = context.user_data['editing_catalog']
    step = process['step']
    user_id = update.effective_user.id
    
    if text == Buttons.CANCEL:
        del context.user_data['editing_catalog']
        await update.message.reply_text(
            "❌ Редактирование отменено.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    # Вся логика редактирования остается без изменений...
    if step == 'search':
        products = CatalogRepository.search_products(text)
        
        if not products:
            await update.message.reply_text(
                f"❌ Товары по запросу '{text}' не найдены.\n"
                f"Попробуйте другой запрос:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        if len(products) == 1:
            process['data']['product'] = products[0]
            process['step'] = 'select_field'
            await show_product_for_editing(update, context, products[0])
        else:
            process['data']['found_products'] = products
            process['step'] = 'select_product'
            
            # Создаем inline-клавиатуру для выбора товара
            keyboard = []
            for idx, product in enumerate(products[:10], 1):
                product_text = f"{product['name']} ({product['category']})"
                if len(product_text) > 30:
                    product_text = f"{product['name'][:25]}... ({product['category']})"
                callback_data = f"{EDIT_PRODUCT_PREFIX}{product['product_id']}"
                keyboard.append([InlineKeyboardButton(f"{idx}. {product_text}", callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit")])
            
            message = "🔍 *Найдены товары:*\n\n"
            for idx, product in enumerate(products[:10], 1):
                message += f"{idx}. {product['name']} ({product['category']})\n"
            
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    # Остальные шаги редактирования остаются без изменений...

async def show_product_for_editing(update: Update, context: CallbackContext, product: dict) -> None:
    """Показать товар для редактирования"""
    message = (
        f"✏️ *Редактирование товара:*\n\n"
        f"🏷️ *Название:* {product['name']}\n"
        f"📁 *Категория:* {product['category']}\n"
        f"📏 *Единица:* {product['unit']}\n"
        f"🔢 *Количество:* {product['default_quantity']}\n"
        f"📝 *Описание:* {product['description'] or 'Нет'}\n"
        f"🆔 *ID:* {product['product_id']}\n\n"
        f"Выберите поле для редактирования:"
    )
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["📁 Категория", "🏷️ Название"],
            ["📏 Единица", "🔢 Количество"],
            ["📝 Описание"],
            ["✅ Сохранить", "❌ Отмена"]
        ],
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def process_edit_category(update: Update, context: CallbackContext) -> None:
    """Обработка изменения категории"""
    if 'editing_category' not in context.user_data:
        return
    
    text = update.message.text.strip()
    process = context.user_data['editing_category']
    step = process['step']
    user_id = update.effective_user.id
    
    if text == Buttons.CANCEL:
        del context.user_data['editing_category']
        await update.message.reply_text(
            "❌ Изменение категории отменено.",
            reply_markup=await get_catalog_keyboard(user_id)
        )
        return
    
    # Вся логика остается без изменений...
    if step == 'select_old':
        if not CatalogRepository.check_category_exists(text):
            await update.message.reply_text(
                f"❌ Категория '{text}' не найдена или не содержит активных товаров.\n"
                f"Введите другую категорию:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        process['data']['old_category'] = text
        process['step'] = 'enter_new'
        
        await update.message.reply_text(
            f"Введите новое название для категории '{text}':",
            reply_markup=get_cancel_keyboard()
        )
    
    elif step == 'enter_new':
        old_category = process['data']['old_category']
        
        if text == old_category:
            await update.message.reply_text(
                "❌ Новое название категории совпадает со старым.\n"
                "Введите другое название:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        process['data']['new_category'] = text
        process['step'] = 'confirm'
        
        products = CatalogRepository.get_category_products(old_category)
        product_count = len(products)
        
        await update.message.reply_text(
            f"⚠️ *Подтвердите изменение категории:*\n\n"
            f"📁 *Старая категория:* {old_category}\n"
            f"📁 *Новая категория:* {text}\n"
            f"📊 *Количество товаров:* {product_count}\n\n"
            f"Все товары категории '{old_category}' будут перемещены в категорию '{text}'.\n\n"
            f"Подтвердить изменение?",
            reply_markup=ReplyKeyboardMarkup(
                [["✅ Да, изменить", "❌ Нет, отменить"]],
                resize_keyboard=True,
                one_time_keyboard=True
            ),
            parse_mode='Markdown'
        )
    
    elif step == 'confirm':
        if text == "✅ Да, изменить":
            old_category = process['data']['old_category']
            new_category = process['data']['new_category']
            
            updated_count = CatalogRepository.update_category(old_category, new_category)
            
            if updated_count > 0:
                await update.message.reply_text(
                    f"✅ *Категория успешно изменена!*\n\n"
                    f"📁 *Старая категория:* {old_category}\n"
                    f"📁 *Новая категория:* {new_category}\n"
                    f"📊 *Обновлено товаров:* {updated_count}",
                    reply_markup=await get_catalog_keyboard(user_id),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при изменении категории.",
                    reply_markup=await get_catalog_keyboard(user_id)
                )
        else:
            await update.message.reply_text(
                "❌ Изменение категории отменено.",
                reply_markup=await get_catalog_keyboard(user_id)
            )
        
        del context.user_data['editing_category']

# ===================== ОБРАБОТЧИК CALLBACK-ЗАПРОСОВ =====================



async def handle_category_deletion(update: Update, context: CallbackContext, category: str) -> None:
    """Обработка выбора категории для удаления"""
    query = update.callback_query
    
    # Инициализируем процесс удаления
    context.user_data['deleting_from_catalog'] = {
        'step': 'select_product',
        'data': {
            'category': category,
            'products': CatalogRepository.get_category_products(category)
        }
    }
    
    products = context.user_data['deleting_from_catalog']['data']['products']
    
    if not products:
        await query.edit_message_text(
            f"❌ В категории '{category}' нет товаров для удаления.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
        del context.user_data['deleting_from_catalog']
        return
    
    # Создаем inline-клавиатуру с товарами
    keyboard = []
    for product in products:
        product_text = f"{product['name']}"
        if len(product_text) > 30:
            product_text = f"{product['name'][:27]}..."
        callback_data = f"{PRODUCT_SELECT_PREFIX}{product['product_id']}"
        keyboard.append([InlineKeyboardButton(f"🗑️ {product_text}", callback_data=callback_data)])
    
    keyboard.append([
        InlineKeyboardButton("🗑️ Удалить ВСЕ товары", callback_data=f"delete_all_category"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")
    ])
    
    message = f"🗑️ *Удаление товаров из категории: {category}*\n\n"
    message += "*Выберите товар для удаления:*\n\n"
    
    for idx, product in enumerate(products, 1):
        message += f"{idx}. 🏷️ *{product['name']}*\n"
        message += f"   📏 {product['unit']} | 🔢 {product['default_quantity']}\n"
        if product['description']:
            message += f"   📝 {product['description']}\n"
        message += f"   🆔 ID: {product['product_id']}\n\n"
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_product_deletion_selection(update: Update, context: CallbackContext, product_id: int) -> None:
    """Обработка выбора товара для удаления"""
    query = update.callback_query
    
    if 'deleting_from_catalog' not in context.user_data:
        await query.edit_message_text(
            "❌ Сессия удаления истекла. Начните заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
        return
    
    products = context.user_data['deleting_from_catalog']['data']['products']
    selected_product = None
    
    for product in products:
        if product['product_id'] == product_id:
            selected_product = product
            break
    
    if not selected_product:
        await query.edit_message_text(
            "❌ Товар не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
        return
    
    context.user_data['deleting_from_catalog']['data']['selected_product'] = selected_product
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"{CONFIRM_DELETE_SINGLE}{product_id}"),
            InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_action")
        ]
    ]
    
    message = (
        f"❓ *Подтвердите удаление товара:*\n\n"
        f"🏷️ *Название:* {selected_product['name']}\n"
        f"📁 *Категория:* {context.user_data['deleting_from_catalog']['data']['category']}\n"
        f"📏 *Единица измерения:* {selected_product['unit']}\n"
        f"🔢 *Стандартное количество:* {selected_product['default_quantity']}\n"
        f"🆔 *ID товара:* {selected_product['product_id']}\n\n"
        f"Это действие можно отменить, установив товар как неактивный.\n"
        f"Удалить товар?"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_delete_all_confirmation(update: Update, context: CallbackContext) -> None:
    """Подтверждение удаления всех товаров категории"""
    query = update.callback_query
    
    if 'deleting_from_catalog' not in context.user_data:
        await query.edit_message_text(
            "❌ Сессия удаления истекла. Начните заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
        return
    
    category = context.user_data['deleting_from_catalog']['data']['category']
    product_count = len(context.user_data['deleting_from_catalog']['data']['products'])
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить ВСЕ", callback_data=f"{CONFIRM_DELETE_ALL}{category}"),
            InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_action")
        ]
    ]
    
    message = (
        f"⚠️ *ВНИМАНИЕ!*\n\n"
        f"Вы собираетесь удалить *ВСЕ товары* из категории: *{category}*\n\n"
        f"Количество товаров для удаления: {product_count}\n\n"
        f"Это действие *НЕЛЬЗЯ* отменить! Все данные будут удалены без возможности восстановления.\n\n"
        f"Подтвердите удаление:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def confirm_delete_product(update: Update, context: CallbackContext, product_id: int) -> None:
    """Подтверждение удаления одного товара"""
    query = update.callback_query
    
    if 'deleting_from_catalog' not in context.user_data:
        await query.edit_message_text(
            "❌ Сессия удаления истекла.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
        return
    
    product_data = context.user_data['deleting_from_catalog']['data']
    selected_product = product_data['selected_product']
    
    success = CatalogRepository.soft_delete_product(product_id)
    
    if success:
        del context.user_data['deleting_from_catalog']
        
        await query.edit_message_text(
            f"✅ *Товар успешно удален!*\n\n"
            f"🏷️ *Название:* {selected_product['name']}\n"
            f"📁 *Категория:* {product_data['category']}\n"
            f"🆔 *ID товара:* {selected_product['product_id']}\n\n"
            f"Товар помечен как неактивный и больше не будет отображаться в справочнике.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при удалении товара.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )

async def confirm_delete_all_products(update: Update, context: CallbackContext, category: str) -> None:
    """Подтверждение удаления всех товаров категории"""
    query = update.callback_query
    
    deleted_count = CatalogRepository.soft_delete_category_products(category)
    
    if deleted_count > 0:
        if 'deleting_from_catalog' in context.user_data:
            del context.user_data['deleting_from_catalog']
        
        await query.edit_message_text(
            f"✅ *Категория полностью очищена!*\n\n"
            f"📁 *Категория:* {category}\n"
            f"🗑️ *Удалено товаров:* {deleted_count}\n\n"
            f"Все товары помечены как неактивные и больше не будут отображаться в справочнике.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при удалении товаров категории.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )

async def show_product_details(update: Update, context: CallbackContext, product_id: int) -> None:
    """Показать детальную информацию о товаре"""
    query = update.callback_query
    
    product = CatalogRepository.get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text(
            "❌ Товар не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog")]
            ])
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"{EDIT_PRODUCT_PREFIX}{product_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"{PRODUCT_SELECT_PREFIX}{product_id}")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"{CATEGORY_BROWSE_PREFIX}{product['category']}")]
    ]
    
    message = (
        f"🏷️ *Детальная информация о товаре:*\n\n"
        f"*Название:* {product['name']}\n"
        f"*Категория:* {product['category']}\n"
        f"*Единица измерения:* {product['unit']}\n"
        f"*Стандартное количество:* {product['default_quantity']}\n"
        f"*Описание:* {product['description'] or 'Нет'}\n"
        f"*ID товара:* {product_id}\n"
        f"*Статус:* {'✅ Активен' if product.get('is_active', True) else '❌ Неактивен'}"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_category_edit_selection(update: Update, context: CallbackContext, category: str) -> None:
    """Обработка выбора категории для редактирования"""
    query = update.callback_query
    
    # Инициализируем процесс редактирования категории
    context.user_data['editing_category'] = {
        'step': 'enter_new',
        'data': {'old_category': category}
    }
    
    await query.edit_message_text(
        f"✏️ *Изменение категории*\n\n"
        f"📁 *Текущая категория:* {category}\n\n"
        f"Введите новое название для категории:",
        parse_mode='Markdown'
    )

async def handle_product_edit_selection(update: Update, context: CallbackContext, product_id: int) -> None:
    """Обработка выбора товара для редактирования"""
    query = update.callback_query
    
    product = CatalogRepository.get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text(
            "❌ Товар не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog_menu")]
            ])
        )
        return
    
    # Инициализируем процесс редактирования
    context.user_data['editing_catalog'] = {
        'step': 'select_field',
        'data': {'product': product}
    }
    
    # Создаем inline-клавиатуру для выбора поля
    keyboard = [
        [
            InlineKeyboardButton("📁 Категория", callback_data=f"{EDIT_FIELD_PREFIX}category"),
            InlineKeyboardButton("🏷️ Название", callback_data=f"{EDIT_FIELD_PREFIX}name")
        ],
        [
            InlineKeyboardButton("📏 Единица", callback_data=f"{EDIT_FIELD_PREFIX}unit"),
            InlineKeyboardButton("🔢 Количество", callback_data=f"{EDIT_FIELD_PREFIX}quantity")
        ],
        [InlineKeyboardButton("📝 Описание", callback_data=f"{EDIT_FIELD_PREFIX}description")],
        [
            InlineKeyboardButton("✅ Сохранить", callback_data=f"{SAVE_EDIT_PREFIX}{product_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit")
        ]
    ]
    
    message = (
        f"✏️ *Редактирование товара:*\n\n"
        f"🏷️ *Название:* {product['name']}\n"
        f"📁 *Категория:* {product['category']}\n"
        f"📏 *Единица:* {product['unit']}\n"
        f"🔢 *Количество:* {product['default_quantity']}\n"
        f"📝 *Описание:* {product['description'] or 'Нет'}\n"
        f"🆔 *ID:* {product_id}\n\n"
        f"*Выберите поле для редактирования:*"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_field_edit_selection(update: Update, context: CallbackContext, field: str) -> None:
    """Обработка выбора поля для редактирования"""
    query = update.callback_query
    
    product = context.user_data['editing_catalog']['data']['product']
    
    if field == 'unit':
        # Создаем клавиатуру с единицами измерения
        keyboard = [
            [
                InlineKeyboardButton("шт", callback_data="set_unit_шт"),
                InlineKeyboardButton("кг", callback_data="set_unit_кг"),
                InlineKeyboardButton("л", callback_data="set_unit_л")
            ],
            [
                InlineKeyboardButton("гр", callback_data="set_unit_гр"),
                InlineKeyboardButton("мл", callback_data="set_unit_мл")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"{EDIT_PRODUCT_PREFIX}{product['product_id']}")]
        ]
        
        await query.edit_message_text(
            f"Выберите единицу измерения для товара '{product['name']}':\n"
            f"Текущая: {product['unit']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Для остальных полей запрашиваем текстовый ввод
        field_names = {
            'category': 'категорию',
            'name': 'название',
            'quantity': 'стандартное количество',
            'description': 'описание'
        }
        
        current_values = {
            'category': product['category'],
            'name': product['name'],
            'quantity': product['default_quantity'],
            'description': product['description'] or 'Нет'
        }
        
        context.user_data['editing_catalog']['step'] = f'edit_{field}'
        
        await query.edit_message_text(
            f"Введите новое значение для {field_names[field]}:\n"
            f"Текущее: {current_values[field]}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data=f"{EDIT_PRODUCT_PREFIX}{product['product_id']}")]
            ])
        )