"""
Обработчики для отображения меню
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.global_keyb import get_main_keyboard
from keyboards.report_keyb import get_main_report_keyboard
from keyboards.admin_keyb import (
    get_admin_keyboard, get_user_management_keyboard,
    get_role_management_keyboard, get_system_settings_keyboard,
    get_features_management_keyboard, get_chat_management_keyboard,
    get_profile_keyboard
)
from keyboards.invent_keyb import get_inventory_keyboard
from keyboards.remind_keyb import get_reminders_keyboard
from keyboards.bonus_keyb import (
    get_bonus_system_keyboard, get_loyalty_program_keyboard,
    get_levels_management_keyboard,
    get_promocodes_keyboard
)
from keyboards.customeers_keyb import get_customer_search_keyboard
from rep_report.report_watch import report_manager
from rep_invent.inventory import (
    create_inventory_list, clear_inventory, add_item,
    show_inventory 
)

from handlers.catalog import (
    manage_catalog, add_to_catalog, edit_catalog_category, edit_catalog_item,
    browse_catalog_for_selection, browse_catalog, del_item_catalog  
)

# Импортируем реальные функции
from rep_bonus.bonus_master import (
    bonus_system, manage_bonus_programs, create_bonus_program, 
    list_bonus_programs  
)
from handlers.handlers_bonus_levels import (
    create_level_conversation, create_level_handler,
    edit_level_handler, level_statistics_handler, list_levels_handler
)

from rep_customer.customers import (
    manage_customers, 
    list_all_customers, check_customer_status, show_my_stat, show_my_bonuses
)

from rep_customer.customer_register import (
    register_customer
)

from rep_customer.customer_purchase import (
    add_purchase
)

from handlers.admin import (
    manage_users, system_stats, admin_panel, manage_users_menu,
    add_user_command, delete_user_command, edit_user_command, show_all_users
)

from handlers.admin_roles import (
    manage_roles_menu, create_role_command, edit_role_command, show_all_roles, set_user_role_command
)

from handlers.admin_edit_user_flow import start_edit_user_flow

from handlers.reminders import (
    manage_reminders
)

# ========== ГЛАВНОЕ МЕНЮ ==========
async def inventory_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню инвентаризации"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Управление инвентаризацией:",
        reply_markup=await get_inventory_keyboard(user_id)
    )

async def reminders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню напоминаний"""
    user_id = update.effective_user.id
    await manage_reminders(update, context)
        
    reply_markup=await get_reminders_keyboard(user_id)

async def customers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню клиентов"""
    # Очищаем контексты списков
    context.user_data.pop('all_customers_list', None)
    context.user_data.pop('search_results', None)
    context.user_data.pop('searching_customer', None)
    
    # Используем вашу реальную функцию
    await manage_customers(update, context)

async def bonus_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню бонусной системы"""
    await bonus_system(update, context)

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню администрирования"""
    await update.message.reply_text(
        "⚙️ *Администрирование*\n\nВыберите раздел для управления:",
        reply_markup=await get_admin_keyboard(),
        parse_mode='Markdown'
    )

async def cleanup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню очистки сообщений"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Управление очисткой:",
        reply_markup= await get_chat_management_keyboard(user_id),
        parse_mode='Markdown'
    )

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню профиля"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Ваш профиль:",
        reply_markup=await get_profile_keyboard(user_id)
    )

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход"""
    await update.message.reply_text("До свидания! 👋", reply_markup=ReplyKeyboardRemove())

#=========инвентаризация и работа со списком
async def add_item(update: Update, context: CallbackContext) -> None:
    """Добавить пользователя"""
    await add_item(update, context)

async def create_list(update: Update, context: CallbackContext) -> None:
    """Редактировать пользователя"""
    await create_inventory_list(update, context)

async def show_inventory(update: Update, context: CallbackContext) -> None:
    """удалить пользователя"""
    await show_inventory(update, context)

async def manage_catalog(update: Update, context: CallbackContext) -> None:
    """главное меню управления каталогом"""
    await manage_catalog(update, context)

async def edit_catalog_item(update: Update, context: CallbackContext) -> None:
    """Редактировать каталог"""
    await edit_catalog_item(update, context)

async def del_item_catalog(update: Update, context: CallbackContext) -> None:
    """удалить товара из каталога"""
    await del_item_catalog(update, context)

async def add_to_catalog(update: Update, context: CallbackContext) -> None:
    """Посмотреть пользователей системы"""
    await add_to_catalog(update, context)

async def edit_catalog_category(update: Update, context: CallbackContext) -> None:
    """Редактирование категории"""
    await edit_catalog_category(update, context)

async def browse_catalog(update: Update, context: CallbackContext) -> None:
    """Просмотреть каталог"""
    await browse_catalog(update, context)

# ========== АДМИНИСТРИРОВАНИЕ - ПОДМЕНЮ ==========


async def system_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню общих настроек"""
    await update.message.reply_text(
        "⚙️ *Общие настройки*\n\nВыберите раздел для настройки:",
        reply_markup=await get_system_settings_keyboard(),
        parse_mode='Markdown'
    )

async def manage_roles_menu(update: Update, context: CallbackContext) -> None:
    """Меню управления ролями"""
    await update.message.reply_text(
        "🎭 *Управление ролями*\n\n"
        "Выберите действие:",
        reply_markup=await get_role_management_keyboard(),
        parse_mode='Markdown'
    )

async def system_settings_menu(update: Update, context: CallbackContext) -> None:
    """Меню общих настроек"""
    await update.message.reply_text(
        "⚙️ *Общие настройки*\n\n"
        "Выберите раздел для настройки:",
        reply_markup=await get_system_settings_keyboard(),
        parse_mode='Markdown'
    )

async def add_user(update: Update, context: CallbackContext) -> None:
    """Добавить пользователя"""
    await add_user_command(update, context)

async def edit_user(update: Update, context: CallbackContext) -> None:
    """Редактировать пользователя"""
    await start_edit_user_flow (update, context)

async def del_user(update: Update, context: CallbackContext) -> None:
    """удалить пользователя"""
    await delete_user_command(update, context)

async def get_all_users(update: Update, context: CallbackContext) -> None:
    """Посмотреть пользователей системы"""
    await show_all_users(update, context)

async def add_roles(update: Update, context: CallbackContext) -> None:
    """Добавить пользователя"""
    await create_role_command(update, context)

async def edit_roles(update: Update, context: CallbackContext) -> None:
    """Редактировать пользователя"""
    await edit_role_command(update, context)

async def get_all_rols(update: Update, context: CallbackContext) -> None:
    """удалить пользователя"""
    await show_all_roles(update, context)


async def chat_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления чатом"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Выберите тип очистки:",
        reply_markup=await get_chat_management_keyboard(user_id)
    )

async def features_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления функциями"""
    await update.message.reply_text(
        "⚡ *Управление функциями системы*\n\nВыберите действие:",
        reply_markup=await get_features_management_keyboard(),
        parse_mode='Markdown'
    )

async def bot_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настроек бота"""
    await update.message.reply_text("Функция настроек бота в разработке")

async def notifications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню уведомлений"""
    await manage_reminders(update, context)

async def system_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика системы"""
    await system_stats(update, context)

async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отчеты"""
    #await report_manager.start_new_report(update, context)
    await update.message.reply_text(
        "*Отчеты*\n\nВыберите действие:",
        reply_markup=await get_main_report_keyboard(),
        parse_mode='Markdown'
    )
# ========== БОНУСНАЯ СИСТЕМА - ПОДМЕНЮ ==========

async def loyalty_program_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню программы лояльности"""
    user_id = update.effective_user.id

    await update.message.reply_text(
        "🎁 *Программа лояльности*\n\nВыберите действие:",
        reply_markup=await get_loyalty_program_keyboard(),
        parse_mode='Markdown'
    )

async def levels_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настройки уровней"""
    await update.message.reply_text(
        "📊 *Настройка уровней*\n\nВыберите действие:",
        reply_markup=await get_levels_management_keyboard(),
        parse_mode='Markdown'
    )

async def programs_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления программами"""
    # Используем вашу реальную функцию
    await manage_bonus_programs(update, context)

async def promocodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню промокодов"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🎫 *Промокоды*\n\nВыберите действие:",
        reply_markup=await get_promocodes_keyboard(),
        parse_mode='Markdown'
    )
# ========== РЕАЛЬНЫЕ ОБРАБОТЧИКИ БОНУСНОЙ СИСТЕМЫ ==========
async def create_program_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание бонусной программы - реальный обработчик"""
    # Используем вашу реальную функцию
    await create_bonus_program(update, context)

async def list_programs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список бонусных программ - реальный обработчик"""
    # Используем вашу реальную функцию
    await list_bonus_programs(update, context)

async def create_level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание уровня"""
    await create_level_handler(update, context)

async def list_levels_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список уровней"""
    await list_levels_handler(update, context)

async def edit_level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение уровня"""
    await edit_level_handler(update, context)

async def level_statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика уровней"""
    await level_statistics_handler(update, context)

async def show_my_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика по клиенту"""
    await show_my_bonuses(update, context)

async def program_statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика программы"""
    await update.message.reply_text("📊 *Статистика программы*\n\nФункция в разработке", parse_mode='Markdown')

async def search_program_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск программы"""
    await update.message.reply_text("🔍 *Поиск программы*\n\nФункция в разработке", parse_mode='Markdown')

async def activate_program_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активация программы"""
    await update.message.reply_text("✅ *Активация программы*\n\nФункция в разработке", parse_mode='Markdown')

async def deactivate_program_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Деактивация программы"""
    await update.message.reply_text("❌ *Деактивация программы*\n\nФункция в разработке", parse_mode='Markdown')

async def program_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки программы"""
    await update.message.reply_text("⚙️ *Настройки программы*\n\nФункция в разработке", parse_mode='Markdown')


async def list_promocodes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список промокодов"""
    await promocodes_menu(update, context)

async def create_promocode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание промокода"""
    await update.message.reply_text("➕ *Создание промокода*\n\nФункция в разработке", parse_mode='Markdown')

async def activate_promocode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активация промокода"""
    await update.message.reply_text("🎯 *Активация промокода*\n\nФункция в разработке", parse_mode='Markdown')

async def promocode_statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика промокодов"""
    await update.message.reply_text("📊 *Статистика промокодов*\n\nФункция в разработке", parse_mode='Markdown')


# ========== КЛИЕНТЫ - РЕАЛЬНЫЕ ОБРАБОТЧИКИ ==========

async def register_customer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регистрация клиента"""
    # Используем вашу реальную функцию
    await register_customer(update, context)

async def search_customer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню поиска клиента"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🔍 *Поиск клиента*\n\nВыберите тип поиска:",
        reply_markup=await get_customer_search_keyboard(),
        parse_mode='Markdown'
    )

async def list_customers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список клиентов"""
    # Используем вашу реальную функцию
    await list_all_customers(update, context)

async def search_customer_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню поиска клиента"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🔍 *Поиск клиента*\n\nВыберите тип поиска:",
        reply_markup=await get_customer_search_keyboard(),
        parse_mode='Markdown'
    )

async def add_purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начисление покупки"""
    # Используем вашу реальную функцию
    await add_purchase(update, context)

async def show_my_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса"""
    # Используем вашу реальную функцию
    await show_my_stat(update, context)

# ========== ПОИСК КЛИЕНТОВ ==========

async def search_by_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по карте"""
    await update.message.reply_text("Функция поиска по карте в разработке")

async def search_by_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по телефону"""
    await update.message.reply_text("Функция поиска по телефону в разработке")

async def search_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по имени"""
    await update.message.reply_text("Функция поиска по имени в разработке")

async def search_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по ID"""
    await update.message.reply_text("Функция поиска по ID в разработке")

async def purchase_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """История покупок"""
    await update.message.reply_text("Функция истории покупок в разработке")


# Кнопки возврата
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    user_id = update.effective_user.id
    # Очищаем контексты
    context.user_data.pop('all_customers_list', None)
    context.user_data.pop('search_results', None)
    context.user_data.pop('searching_customer', None)
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=await get_main_keyboard(user_id)
    )

async def back_to_customers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к клиентам"""
    await customers_menu(update, context)

async def back_to_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к бонусной системе"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🎁 *Бонусная система*",
        reply_markup=await get_bonus_system_keyboard(user_id)
    )

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к администрированию"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "⚙️ *Администрирование*",
        reply_markup=await get_admin_keyboard()
    )

async def back_to_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к настройкам"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "⚙️ *Общие настройки*",
        reply_markup=await get_system_settings_keyboard(user_id)
    )

async def back_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к управлению чатом"""
    await chat_management_menu(update, context)


# Профиль
async def profile_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о профиле"""
    user_id = update.effective_user.id
    from handlers.admin_roles_class import role_manager, UserRole
    
    role = await role_manager.get_user_role(user_id)
    await update.message.reply_text(
        f"👤 Ваш профиль\n\n"
        f"ID: {user_id}\n"
        f"Роль: {role.value}\n\n"
        f""
        "Используйте кнопки ниже для управления профилем."
    )
# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

async def back_to_admin(update: Update, context: CallbackContext) -> None:
    """Возврат в панель администратора"""
    await admin_panel(update, context)

async def back_to_user_management(update: Update, context: CallbackContext) -> None:
    """Возврат в меню управления пользователями"""
    await manage_users_menu(update, context)

async def back_to_role_management(update: Update, context: CallbackContext) -> None:
    """Возврат в меню управления ролями"""
    await manage_roles_menu(update, context)

# Заглушки для функций в разработке
async def activate_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активация клиента"""
    await update.message.reply_text("Функция активации клиента в разработке")

async def deactivate_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Деактивация клиента"""
    await update.message.reply_text("Функция деактивации клиента в разработке")

async def manage_users_menu(update: Update, context: CallbackContext) -> None:
    """Меню управления пользователями"""
    await update.message.reply_text(
        "👥 *Управление пользователями*\n\n"
        "Выберите действие:",
        reply_markup=await get_user_management_keyboard(),
        parse_mode='Markdown'
    )

async def features_management_menu(update: Update, context: CallbackContext) -> None:
    """Меню управления функциями системы"""
    await update.message.reply_text(
        "⚡ *Управление функциями системы*\n\n"
        "Выберите действие:",
        reply_markup=await get_features_management_keyboard(),
        parse_mode='Markdown'
    )

async def chat_management_detailed_menu(update: Update, context: CallbackContext) -> None:
    """Детальное меню управления чатом"""
    await update.message.reply_text(
        "💬 *Управление чатом*\n\n"
        "Выберите действие:",
        reply_markup=await get_chat_management_keyboard(),
        parse_mode='Markdown'
    )