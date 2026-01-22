from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from config.buttons import Buttons
from keyboards.global_keyb import get_cancel_keyboard
from keyboards.invent_keyb import get_catalog_keyboard
from .catalog_cervices_class import CatalogRepository
from handlers.catalog import show_product_for_editing, save_to_catalog, delete_single_product, delete_all_category_products, PRODUCT_SELECT_PREFIX, EDIT_PRODUCT_PREFIX
from utils.telegram_utils import send_or_edit_message
import logging

logger = logging.getLogger(__name__)

class CatalogProcessManager:

    def logger(self):
        self.logger = logging.getLogger(__name__)

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
                    text=f"❌ В категории '{text}' нет активных товаров.\nВведите другую категорию:",
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
            
            await send_or_edit_message(
                update=update,
                text=message,
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
                    reply_markup=await get_catalog_keyboard(user_id),
                    delete_previous=True
                )