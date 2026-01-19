from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
import logging
from datetime import datetime
from handlers.admin_roles_class import role_manager, Permission
from config.buttons import Buttons
from rep_invent.inventory_services_class import inventory_service
from keyboards.global_keyb import get_main_keyboard, get_cancel_keyboard
from keyboards.invent_keyb import get_inventory_keyboard, get_units_keyboard
from handlers.catalog import browse_catalog_for_selection

logger = logging.getLogger(__name__)

async def add_item(update: Update, context: CallbackContext) -> None:
    """Начало добавления товара в инвентаризацию"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await update.message.reply_text(
            "❌ У вас нет прав для добавления товаров.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Проверяем наличие активного списка
    active_list = inventory_service.get_active_user_list(user_id)
    
    if not active_list:
        # Создаем новый список инвентаризации
        list_name = f"Инвентаризация от {datetime.now().strftime('%d.%m.%Y')}"
        active_list = inventory_service.create_inventory_list(user_id, list_name)
        
        if not active_list:
            await update.message.reply_text(
                "❌ Не удалось создать список инвентаризации.",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
    
    # Спрашиваем, как добавлять товар
    await update.message.reply_text(
        "➕ *Добавление товара в инвентаризацию*\n\n"
        f"Список: {active_list['list_name']}\n"
        f"Дата: {active_list['created_at']}\n\n"
        "Выберите способ добавления:",
        reply_markup=ReplyKeyboardMarkup(
            [
                [Buttons.SELECT_CATALOG, Buttons.ADD_ITEM],
                [Buttons.BACK_TO_INVENTORY]
            ],
            resize_keyboard=True
        ),
        parse_mode='Markdown'
    )
    
    context.user_data['adding_item_method'] = True
    context.user_data['active_list_id'] = active_list['list_id']

async def process_item_input(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ввод данных товара"""
    if 'item_process' not in context.user_data:
        # Проверяем выбор метода добавления
        if context.user_data.get('adding_item_method', False):
            text = update.message.text.strip()
            user_id = update.effective_user.id
            
            if text == Buttons.SELECT_CATALOG:
                del context.user_data['adding_item_method']
                await browse_catalog_for_selection(update, context)
                return
            elif text == Buttons.ADD_ITEM:
                del context.user_data['adding_item_method']
                # Стандартный процесс добавления
                context.user_data['item_process'] = {
                    'step': 'name',
                    'data': {}
                }
                await update.message.reply_text(
                    "Введите название товара:",
                    reply_markup=get_cancel_keyboard()
                )
                return
            elif text == Buttons.BACK_TO_INVENTORY:
                del context.user_data['adding_item_method']
                await update.message.reply_text(
                    "Управление инвентаризацией:",
                    reply_markup=await get_inventory_keyboard(user_id)
                )
                return
        
        return
    
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "❌ Отмена":
        if 'item_process' in context.user_data:
            del context.user_data['item_process']
        await update.message.reply_text(
            "Добавление отменено.",
            reply_markup=await get_inventory_keyboard(user_id)
        )
        return
    
    if 'item_process' not in context.user_data:
        return
    
    process = context.user_data['item_process']
    
    if process['step'] == 'name':
        await _process_name(update, context, text)
    elif process['step'] == 'quantity':
        await _process_quantity(update, context, text)
    elif process['step'] == 'unit':
        await _process_unit(update, context, text)

async def _process_name(update: Update, context: CallbackContext, name: str) -> None:
    """Обрабатывает название"""
    if not name:
        await update.message.reply_text("Название не может быть пустым:")
        return
    
    context.user_data['item_process']['name'] = name
    context.user_data['item_process']['step'] = 'quantity'
    
    await update.message.reply_text("Введите количество:")

async def _process_quantity(update: Update, context: CallbackContext, quantity_text: str) -> None:
    """Обрабатывает количество"""
    try:
        quantity = float(quantity_text.replace(',', '.'))
        if quantity <= 0:
            await update.message.reply_text("Количество > 0:")
            return
        
        context.user_data['item_process']['quantity'] = quantity
        context.user_data['item_process']['step'] = 'unit'
        
        await update.message.reply_text(
            "Выберите единицу измерения:",
            reply_markup=get_units_keyboard()
        )
        
    except ValueError:
        await update.message.reply_text("Введите число:")

async def _process_unit(update: Update, context: CallbackContext, unit: str) -> None:
    """Обрабатывает единицу измерения и сохраняет"""
    process = context.user_data.get('item_process', {})
    user_id = update.effective_user.id
    list_id = context.user_data.get('active_list_id')
    
    if not list_id:
        await update.message.reply_text("Ошибка: список не найден")
        return
    
    try:
        # Получаем данные о товаре
        item_data = {}
        
        # Если товар из справочника
        if 'selected_product' in context.user_data:
            product = context.user_data['selected_product']
            item_name = product['name']
            quantity = product.get('quantity', 1)
            description = product.get('description', '')
            
            # Удаляем временные данные
            del context.user_data['selected_product']
        # Если товар вводился вручную
        elif 'item_process' in context.user_data:
            item_name = process.get('name', '')
            quantity = process.get('quantity', 0)
            description = f"Добавлено вручную"
        else:
            await update.message.reply_text("Ошибка: данные товара не найдены")
            return
        
        if not item_name or quantity <= 0:
            await update.message.reply_text("Ошибка: некорректные данные товара")
            logger.debug(f"Ошибка: некорректные данные товара: {item_name}, {quantity}")
            return
        
        # Используем сервис для сохранения
        success = inventory_service.add_item_to_list(
            list_id=list_id,
            name=item_name,
            quantity=quantity,
            unit=unit,
            description=description
        )
        
        if not success:
            await update.message.reply_text("Ошибка при сохранении товара")
            return
        
        # Очищаем данные процесса
        if 'item_process' in context.user_data:
            del context.user_data['item_process']
        
        await update.message.reply_text(
            f"✅ Товар добавлен!\n{item_name} - {quantity} {unit}",
            reply_markup=await get_inventory_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await update.message.reply_text("Ошибка сохранения.")

async def show_inventory(update: Update, context: CallbackContext) -> None:
    """Показывает список товаров"""
    user_id = update.effective_user.id
    
    try:
        active_list = inventory_service.get_active_user_list(user_id)
        if not active_list:
            await update.message.reply_text(
                "У вас нет активного списка инвентаризации.\n"
                "Создайте новый список через 'Добавить товар'",
                reply_markup=await get_inventory_keyboard(user_id)
            )
            return
        
        items = inventory_service.get_list_items(active_list['list_id'])
        
        if not items:
            await update.message.reply_text(
                f"📦 Список пуст\n\n"
                f"Список: {active_list['list_name']}\n"
                f"Дата создания: {active_list['created_at']}"
            )
        else:
            inventory_text = "\n".join(
                [f"• {item['name']} - {item['expected_quantity']} {item['unit']}" 
                 for item in items]
            )
            await update.message.reply_text(
                f"📦 *Ваш список инвентаризации*\n\n"
                f"*Список:* {active_list['list_name']}\n"
                f"*Дата проведения:* {active_list['created_at']}\n\n"
                f"*Товары:*\n{inventory_text}\n\n"
                f"Всего товаров: {len(items)}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Ошибка показа списка: {e}")
        await update.message.reply_text("Ошибка загрузки списка.")

# handlers/inventory.py
#def get_user_list(user_id):
#    """Получаем список активных пользователей"""
#    try:
#        with sqlite_connection() as conn:
#            cursor = conn.cursor()
#            cursor.execute('''
#                SELECT list_id FROM inventory_lists
#                WHERE user_id = ? AND is_active = 1
#                ''', (user_id,))
#            return cursor.fetchone()
#    except sqlite3.Error as e:
#        logger.error(f"Ошибка получения списка: {e}")
#        return None

async def clear_inventory(update: Update, context: CallbackContext) -> None:
    """Очищает список товаров"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await update.message.reply_text(
            "❌ У вас нет прав для очистки списка.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    try:
        active_list = inventory_service.get_active_user_list(user_id)
        if not active_list:
            await update.message.reply_text("Нет активного списка для очистки")
            return
        
        success = inventory_service.clear_list(active_list['list_id'])
        
        if success:
            await update.message.reply_text("✅ Список очищен")
        else:
            await update.message.reply_text("❌ Ошибка при очистке списка")
            
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")
        await update.message.reply_text("Ошибка очистки.")

async def create_inventory_list(update: Update, context: CallbackContext) -> None:
    """Создает новый список инвентаризации"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await update.message.reply_text(
            "❌ У вас нет прав для создания списков инвентаризации.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Создаем новый список с датой
    list_name = f"Инвентаризация от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    new_list = inventory_service.create_inventory_list(user_id, list_name)
    
    if new_list:
        await update.message.reply_text(
            f"✅ *Создан новый список инвентаризации*\n\n"
            f"*Название:* {new_list['list_name']}\n"
            f"*Дата проведения:* {new_list['created_at']}\n"
            f"*ID списка:* {new_list['list_id']}",
            parse_mode='Markdown',
            reply_markup=await get_inventory_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось создать список инвентаризации",
            reply_markup=await get_inventory_keyboard(user_id)
        )

async def deactivate_inventory_list(update: Update, context: CallbackContext) -> None:
    """Деактивирует текущий список инвентаризации"""
    user_id = update.effective_user.id
    
    if not await role_manager.has_permission(user_id, Permission.MANAGE_INVENTORY):
        await update.message.reply_text(
            "❌ У вас нет прав для деактивации списков.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    try:
        active_list = inventory_service.get_active_user_list(user_id)
        if not active_list:
            await update.message.reply_text("Нет активного списка для деактивации")
            return
        
        success = inventory_service.deactivate_list(active_list['list_id'])
        
        if success:
            await update.message.reply_text(
                f"✅ Список деактивирован\n"
                f"'{active_list['list_name']}'",
                reply_markup=await get_inventory_keyboard(user_id)
            )
        else:
            await update.message.reply_text("❌ Ошибка при деактивации списка")
            
    except Exception as e:
        logger.error(f"Ошибка деактивации: {e}")
        await update.message.reply_text("Ошибка деактивации.")