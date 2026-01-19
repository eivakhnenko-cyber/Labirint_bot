from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, CallbackContext, CallbackQueryHandler
import logging

from config.buttons import Buttons
from rep_customer.customers import *
logger = logging.getLogger(__name__)

VIEW_CUSTOMER_PREFIX = "view_customer_"
CLOSE_CUSTOMER_LIST = "close_customer_list"
BACK_TO_LIST = "back_to_customer_list"
CLOSE_DETAILS = "close_details"

class HandCustManager:
    """Обработчики с функционалом Клиентов"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def handle_customer_callback(self, update: Update, context: CallbackContext) -> None:
        """Обработчик inline-кнопок клиентов"""
    
        query = update.callback_query
        
        try:
            await query.answer()
            callback_data = query.data
            
            # 1. ЗАКРЫТЬ СПИСОК КЛИЕНТОВ
            if callback_data == CLOSE_CUSTOMER_LIST:
                await query.edit_message_text("❌ Список закрыт")
                return
            
            # 2. ЗАКРЫТЬ ДЕТАЛИ
            elif callback_data == CLOSE_DETAILS:
                await query.delete_message()
                return
            
            # 3. НАЗАД К СПИСКУ
            elif callback_data == BACK_TO_LIST:
                # Получаем сохраненный список клиентов
                customers = (context.user_data.get('all_customers_list') or 
                            context.user_data.get('search_results'))
                
                if customers:
                    await show_customer_list(update, context, customers)
                else:
                    await query.edit_message_text("❌ Список клиентов не найден")
                return
            
            # 4. ПРОСМОТР КЛИЕНТА
            elif callback_data.startswith(VIEW_CUSTOMER_PREFIX):
                customer_id = int(callback_data.replace(VIEW_CUSTOMER_PREFIX, ""))
                
                # Получаем клиента из базы (нужен импорт вашего менеджера)
                from rep_customer.customer_manager_class import customer_manager  # или ваш менеджер
                customer = customer_manager.find_customer_by_id(customer_id)
                
                if not customer:
                    await query.edit_message_text(f"❌ Клиент с ID {customer_id} не найден")
                    return
                
                await show_customer_details(query, context, customer)
        except Exception as e:
            self.logger.error(f"Ошибка обработки callback клиента: {e}")
            try:
                await query.edit_message_text("❌ Ошибка при обработке запроса")
            except:
                pass

    async def handle_customer_selection(self, update: Update, context: CallbackContext) -> None:
        """Обработка выбора клиента из списка"""
        text = update.message.text.strip()
        
        self.logger.info(f"Выбор клиента: '{text}'")
        self.logger.info(f"Контекст: {list(context.user_data.keys())}")
        
        # Проверяем навигационные кнопки
        if text == Buttons.SEARCH_CUSTOMER or text == "🔍 Поиск клиента":
            await search_customer(update, context)
            return
        elif text == Buttons.BACK_TO_CUSTOMERS or text == "🔙 Назад к клиентам":
            await manage_customers(update, context)
            return
        elif text == Buttons.ADD_PURCHASE:
            from rep_customer.customer_purchase import add_purchase
            await add_purchase(update, context)
            return
        elif text == "🔙 Назад к результатам поиска" or text == "🔙 Назад к списку клиентов":
            # Восстанавливаем предыдущий список
            if 'search_results' in context.user_data or 'all_customers_list' in context.user_data:
                await list_all_customers(update, context)
            else:
                await manage_customers(update, context)
            return
        elif text == Buttons.CUSTOMERS_LIST:
            # Если нажата кнопка "Список клиентов", показываем список
            await list_all_customers(update, context)
            return
        
        # Определяем, какой список использовать
        customers = None
        if 'search_results' in context.user_data:
            customers = context.user_data['search_results']
            list_type = 'search'
        elif 'all_customers_list' in context.user_data:
            customers = context.user_data['all_customers_list']
            list_type = 'all'
        else:
            await update.message.reply_text(
                "Сессия истекла. Начните поиск заново.",
                reply_markup=await get_customers_main_keyboard()
            )
            return
        
        if not customers:
            await update.message.reply_text(
                "Список клиентов пуст. Начните поиск заново.",
                reply_markup=await get_customers_main_keyboard()
            )
            return
        
        # Пытаемся извлечь ID клиента из текста
        try:
            customer_id = None
            customer_name = None
            
            if text.startswith("👤 "):
                # Формат: "👤 {id}: {name}"
                parts = text.split(":")
                if parts:
                    # Извлекаем ID из части перед двоеточием
                    id_part = parts[0].replace("👤 ", "").strip()
                    try:
                        customer_id = int(id_part)
                    except ValueError:
                        # Если не удалось преобразовать в int, пытаемся извлечь цифры
                        import re
                        numbers = re.findall(r'\d+', id_part)
                        if numbers:
                            customer_id = int(numbers[0])
                    
                    if len(parts) > 1:
                        customer_name = parts[1].strip()
            
            self.logger.info(f"Парсинг: id={customer_id}, name={customer_name}, text='{text}'")
            
            # Ищем клиента в списке
            customer_found = None
            
            if customer_id:
                # Ищем по ID
                for customer in customers:
                    if customer.get('customer_id') == customer_id:
                        customer_found = customer
                        break
            else:
                # Ищем по имени (частичное совпадение)
                for customer in customers:
                    if text in customer.get('username', ''):
                        customer_found = customer
                        break
            
            if customer_found:
                self.logger.info(f"Найден клиент в списке: {customer_found.get('customer_id')}")
                
                # Проверяем, есть ли все необходимые поля
                if 'bonus_program_id' not in customer_found or 'total_purchases' not in customer_found:
                    self.logger.info("Данные клиента неполные, загружаем из БД...")
                    # Загружаем полные данные из БД
                    full_customer = await customer_manager.find_customer_by_id(
                        customer_found['customer_id']
                    )
                    if full_customer:
                        await show_customer_details(update, context, full_customer)
                    else:
                        await update.message.reply_text(
                            "❌ Не удалось загрузить полные данные клиента.",
                            reply_markup=await get_customers_main_keyboard()
                        )
                else:
                    await show_customer_details(update, context, customer_found)
            else:
                self.logger.warning(f"Клиент не найден в списке, пробуем найти в БД напрямую...")
                
                # Пробуем найти клиента по ID в БД
                if customer_id:
                    customer = await customer_manager.find_customer_by_id(customer_id)
                    if customer:
                        await show_customer_details(update, context, customer)
                    else:
                        # Пробуем найти по имени
                        if customer_name:
                            search_results = await customer_manager.find_customers_by_search_query(customer_name)
                            if search_results and len(search_results) == 1:
                                await show_customer_details(update, context, search_results[0])
                            elif search_results and len(search_results) > 1:
                                await show_customer_list(update, context, search_results, customer_name)
                            else:
                                await update.message.reply_text(
                                    f"❌ Клиент с ID {customer_id} не найден.",
                                    reply_markup=await get_customers_main_keyboard()
                                )
                        else:
                            await update.message.reply_text(
                                f"❌ Клиент с ID {customer_id} не найден.",
                                reply_markup=await get_customers_main_keyboard()
                            )
                else:
                    # Пробуем найти по тексту как поисковому запросу
                    search_results = await customer_manager.find_customers_by_search_query(text)
                    if search_results and len(search_results) == 1:
                        await show_customer_details(update, context, search_results[0])
                    elif search_results and len(search_results) > 1:
                        await show_customer_list(update, context, search_results, text)
                    else:
                        await update.message.reply_text(
                            "❌ Клиент не найден.",
                            reply_markup=await get_customers_main_keyboard()
                        )
                    
        except Exception as e:
            self.logger.error(f"Ошибка выбора клиента: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Ошибка при выборе клиента. Попробуйте снова.",
                reply_markup=await get_customers_main_keyboard()
            )

hand_cust_manager = HandCustManager()