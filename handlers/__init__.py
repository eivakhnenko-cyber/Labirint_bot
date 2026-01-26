# handlers/__init__.py
import sys
import os

if __name__ == "__main__":
    print("Это модуль, не запускай напрямую!")
    print("Запускай через: python main.py")
    sys.exit(1)
    
from .start import start
from rep_invent.inventory import (
    add_item, process_item_input, 
    show_inventory, clear_inventory
)
from .reminders import (
    manage_reminders, start_reminders, stop_reminders, 
    setup_schedule, show_reminders_status, 
    handle_custom_reminder_input, handle_time_input, 
    handle_schedule_day_selection
)
from .cleanup import (
    cleanup_all_messages, 
    handle_cleanup_confirmation
)

# Экспорт функций из bonus.py
from rep_bonus.bonus_master import (
    bonus_system,
    create_bonus_program,
    list_bonus_programs,
    manage_bonus_programs,
    process_program_creation
)

# Экспорт функций из customers.py
from rep_customer.customers import (
    manage_customers, 
    list_all_customers,
    check_customer_status,
    search_customer,
    process_customer_search,
    show_customer_details, show_my_bonuses
)
from handlers.handlers_customer import (
    hand_cust_manager
)
from rep_customer.customer_purchase import (
    add_purchase, process_purchase, save_purchase
)
from rep_customer.customer_register import (
    register_customer,
    process_customer_registration,
)


# Экспорт функций из menus.py
from .menus import *

__all__ = [
    'start',
    'add_item', 'process_item_input', 'show_inventory', 'clear_inventory',
    'manage_reminders', 'start_reminders', 'stop_reminders', 'setup_schedule', 
    'handle_schedule_type_selection', 'handle_custom_reminder_input', 
    'handle_schedule_day_selection', 'handle_time_input', 
    'show_reminders_status', 'handle_reminder_type_selection'
    'show_cleanup_options', 'cleanup_all_messages', 
    'handle_cleanup_confirmation', 'manage_customers',
    'register_customer', 'add_purchase', 'process_customer_registration',
    'process_purchase', 'save_purchase', 'list_all_customers',
    'check_customer_status', 'search_customer', hand_cust_manager,
    'process_customer_search', 'handle_customer_selection', show_customer_details, show_my_bonuses,
    'show_customer_list', 'bonus_system', 'create_bonus_program',
    'list_bonus_programs', 'manage_bonus_programs', 'process_program_creation'
]