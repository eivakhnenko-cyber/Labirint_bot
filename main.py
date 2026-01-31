import logging
from handlers.admin_edit_user_flow import edit_user_conversation_handler, start_edit_user_flow
from handlers.callback_handler import handle_callback_query
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import ReplyKeyboardRemove, BotCommandScopeChat
# Импортируем настройку команд
from bot_comands import set_default_commands, set_user_commands  # Добавьте эту строку

from bot_config import TELEGRAM_BOT_TOKEN as TOKEN
from database import init_db
from handlers.start import start, check_and_show_logo

from handlers.admin_roles_class import role_manager

# Импорт обработчиков
from handlers.admin import (
    admin_panel, manage_users, my_role, system_stats, add_user_command, delete_user_command, 
    edit_user_command, help_command,
    make_admin, show_all_users
)
from handlers.admin_roles import (
    create_role_command, edit_role_command, set_user_role_command, show_all_roles
)

from rep_customer.customers import (
    list_all_customers, show_my_stat,
    show_customer_details, show_my_bonuses
)
from rep_customer.customers_inline import(
    show_customer_list_inline
)
from handlers.handlers_customer import (
    hand_cust_manager, VIEW_CUSTOMER_PREFIX, 
    CLOSE_CUSTOMER_LIST, BACK_TO_LIST,CLOSE_DETAILS
)
from rep_customer.customer_register import (
    register_customer
)
from rep_customer.customer_search import (
    search_manager
)
from rep_customer.customer_purchase import (
    add_purchase
)
from rep_bonus.bonus_master import (
    manage_bonus_programs, create_bonus_program, list_bonus_programs,
    bonus_system
)
from handlers.handlers_bonus_levels import (
    create_level_conversation, create_level_handler, list_levels_handler, level_statistics_handler, edit_level_handler, delete_level_handler
)
from rep_bonus.bonus_levels_delete import (
    handle_delete_level_callback,
    DELETE_LEVEL_CALLBACK_PREFIX,
    CONFIRM_DELETE_CALLBACK_PREFIX,
    CANCEL_DELETE_CALLBACK
)
from rep_invent.inventory import (
    add_item, show_inventory, clear_inventory, create_inventory_list,
    browse_catalog_for_selection
)
from handlers.catalog import (
    manage_catalog, browse_catalog_for_selection, add_to_catalog, edit_catalog_category,
    edit_catalog_item, browse_catalog, del_item_catalog
)
from rep_catalog.catalog_process import(
    CatalogProcessManager
)

from handlers.reminders import (
    manage_reminders, start_reminders, stop_reminders,
    setup_reminder_type, setup_schedule, show_reminders_status,
    check_jobs, reload_reminders
)
from handlers.cleanup import (
    cleanup_own_messages, cleanup_all_messages, request_message_count
)

# Импорт меню-обработчиков
from handlers.menus import (
    inventory_menu, reminders_menu, customers_menu, bonus_menu,
    admin_menu, profile_menu, exit_command,
    manage_users_menu, manage_roles_menu, system_settings_menu,
    chat_management_menu, features_management_menu,
    loyalty_program_menu, levels_settings_menu, programs_management_menu,
    promocodes_menu, search_customer_menu, create_bonus_program,
    back_to_main, back_to_customers, back_to_bonus, back_to_admin,
    back_to_settings, back_to_chat, cleanup_menu,
    profile_info, activate_customer, deactivate_customer, create_program_handler, list_programs_handler,
    register_customer_handler, show_all_customers,
    add_purchase_handler, check_customer_status, tools_menu,
    search_by_card, search_by_phone, search_by_name, search_by_id,
    purchase_history, bot_settings_menu, notifications_menu, report_menu
)
from rep_report.report_watch import report_manager

# Импорт обработчика сообщений
from handlers.message_handler import create_message_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error("Ошибка в обработчике:", exc_info=context.error)

    if update and hasattr(update, 'message'):
        try:
            user_id = update.effective_user.id
            from keyboards.global_keyb import get_main_keyboard
            await update.message.reply_text(
                "Произошла ошибка. Попробуйте позже.",
                reply_markup=await get_main_keyboard(user_id)
            )
        except:
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def post_init(application):
    """Функция, выполняемая после инициализации бота"""
    await set_default_commands(application)
    logger.info("✅ Меню команд бота установлено")

def main():
    """Основная функция"""
    
    check_and_show_logo()
        
    # Инициализация БД
    init_db()
    
    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()
    
    if not application.job_queue:
        logger.error("JobQueue не доступен!")
        return
    
    logger.info("JobQueue успешно инициализирован")
    
    application.post_init = post_init

    # Реестр всех обработчиков
    handlers_registry = {
        # Команды
        'start': start,
        'my_role': my_role,
        'set_user_role_command': set_user_role_command,
        'manage_users': manage_users,
        'system_stats': system_stats,
        'tools_menu': tools_menu,
        'make_admin': make_admin,
        
        # Главное меню
        'inventory_menu': inventory_menu,
        'reminders_menu': reminders_menu,
        'customers_menu': customers_menu,
        'bonus_menu': bonus_menu,
        'admin_menu': admin_menu,
        'profile_menu': profile_menu,
        'exit_command': exit_command,
        
        # Инвентаризация
        'show_inventory': show_inventory,
        'add_item': add_item,
        'create_list': create_inventory_list,
        #'compare_inventory': compare_inventory,
        'clear_inventory': clear_inventory,
        #'confirm_inventory': confirm_inventory,
        'manage_catalog': manage_catalog,
        'selecting_from_catalog': browse_catalog_for_selection,
        'browse_catalog': browse_catalog,
        'add_to_catalog': add_to_catalog,
        'edit_catalog_item': edit_catalog_item,
        'edit_catalog_category': edit_catalog_category,
        'del_item_catalog': del_item_catalog,

        # Напоминания
        'show_reminders_status': show_reminders_status,
        'setup_schedule': setup_schedule,
        'setup_reminder_type': setup_reminder_type,
        'start_reminders': start_reminders,
        'stop_reminders': stop_reminders,
        'check_jobs': check_jobs,
        'reload_reminders': reload_reminders,
             
        # Очистка чата
        'cleanup_menu': cleanup_menu,
        'cleanup_all_messages': cleanup_all_messages,
        'cleanup_own_messages': cleanup_own_messages,
        'request_message_count': request_message_count,
        
        # ========== БОНУСНАЯ СИСТЕМА ==========
        'bonus_menu': bonus_menu,  # Это вызовет вашу bonus_system функцию
        'bonus_system': bonus_system,
        'loyalty_program_menu': loyalty_program_menu,
        'levels_settings_menu': levels_settings_menu,
        'programs_management_menu': programs_management_menu,
        'promocodes_menu': promocodes_menu,
        'manage_bonus_programs': manage_bonus_programs,
        'create_bonus_program': create_bonus_program,
        'list_bonus_programs': list_bonus_programs,

        # ========== УРОВНИ БОНУСНОЙ ПРОГРАММЫ ==========
        'create_level_handler': create_level_handler,
        'list_levels_handler': list_levels_handler,
        'edit_level_handler': edit_level_handler,
        'level_statistics_handler': level_statistics_handler,

         # Реальные обработчики бонусной системы
        'create_program_handler': create_program_handler,  # ✅
        'list_programs_handler': list_programs_handler,    # ✅
        'delete_level_handler': delete_level_handler,

         # ========== КЛИЕНТЫ ==========
        'register_customer_handler': register_customer_handler,
        'search_customer_menu': search_customer_menu,
        'add_purchase_handler': add_purchase_handler,
        'register_customer': register_customer,
        'add_purchase': add_purchase,
        'list_all_customers': show_all_customers,
        'show_my_stat': show_my_stat,
        'search_customer': search_manager.search_customer,
        'show_customer_list': show_customer_list_inline,
        'show_customer_details': show_customer_details,
        'show_my_bonuses': show_my_bonuses,


        # Подменю администрирования
        'manage_users_menu': manage_users_menu,
        'manage_roles_menu': manage_roles_menu,
        'system_settings_menu': system_settings_menu,
        'chat_management_menu': chat_management_menu,
        'features_management_menu': features_management_menu,
        'bot_settings_menu': bot_settings_menu,
        'notifications_menu': notifications_menu,

        # ========== Пользователи системы ==========
        'get_all_users': show_all_users,
        'add_user': add_user_command,
        'edit_user': start_edit_user_flow,
        'del_user': delete_user_command,

        # ========== Управление ролями ==========
        'get_all_rols': show_all_roles,
        'add_rols': create_role_command,
        'edit_rols': edit_role_command,
        
        # Кнопки возврата
        'back_to_main': back_to_main,
        'back_to_customers': back_to_customers,
        'back_to_bonus': back_to_bonus,
        'back_to_admin': back_to_admin,
        'back_to_settings': back_to_settings,
        'back_to_chat': back_to_chat,
        
        # Профиль
        'profile_info': profile_info,
        
        # Активация/деактивация клиентов
        'activate_customer': activate_customer,
        'deactivate_customer': deactivate_customer,
        
        # Поиск клиентов
        'search_by_card': search_by_card,
        'search_by_phone': search_by_phone,
        'search_by_name': search_by_name,
        'search_by_id': search_by_id,
        'purchase_history': purchase_history,

        # Отчетность
        'report_menu': report_menu,
        'start_report': report_manager.start_new_report,
        'show_report': report_manager.show_report,
        'stop_watch': report_manager.close_report,
        'report_history': report_manager.show_report_history,
    }
        
    # Создаем обработчик сообщений

    message_handler = create_message_handler(handlers_registry)
    
    application.add_handler(edit_user_conversation_handler)
    application.add_handler(CallbackQueryHandler(report_manager.handle_callback, pattern=f"^(report_|main_menu)"))
    application.add_handler(CallbackQueryHandler(hand_cust_manager.handle_customer_callback, pattern=f"^({VIEW_CUSTOMER_PREFIX}|{CLOSE_CUSTOMER_LIST}|{BACK_TO_LIST}|{CLOSE_DETAILS})"))
    application.add_handler(CallbackQueryHandler(handle_delete_level_callback, pattern=f"^({DELETE_LEVEL_CALLBACK_PREFIX}|{CONFIRM_DELETE_CALLBACK_PREFIX}|{CANCEL_DELETE_CALLBACK})"))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(create_level_conversation)
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("role", my_role))
    application.add_handler(CommandHandler("setrole", set_user_role_command))
    application.add_handler(CommandHandler("users", manage_users))
    application.add_handler(CommandHandler("stats", system_stats))
    application.add_handler(CommandHandler("makeadmin", make_admin))
    application.add_handler(CommandHandler("adduser", add_user_command))
    application.add_handler(CommandHandler("edituser", edit_user_command))
    application.add_handler(CommandHandler("deluser", delete_user_command))
    application.add_handler(CommandHandler("deletelevel", delete_level_handler))

    
    # Регистрация основного обработчика сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Бот запущен...")
    application.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )

if __name__ == "__main__":
    main()