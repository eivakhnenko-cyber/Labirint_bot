from telegram import ReplyKeyboardMarkup
from config.buttons import Buttons

async def get_customers_main_keyboard():
    """Главное меню клиентов"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.REGISTER_CUSTOMER, Buttons.CUSTOMERS_LIST],
            [Buttons.SEARCH_CUSTOMER, Buttons.CUSTOMER_STATISTICS],
            [Buttons.BACK_TO_MAIN]
        ],
        resize_keyboard=True
    )

async def get_customers_purch_keyboard():
    """Меню управления клиентами"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.ADD_PURCHASE, Buttons.PURCHASE_HISTORY],
            [Buttons.ACTIVATE_CUSTOMER, Buttons.DEACTIVATE_CUSTOMER],
            [Buttons.BACK_TO_CUSTOMERS]
        ],
        resize_keyboard=True
    )

async def get_customer_search_keyboard():
    """Меню поиска клиента"""
    return ReplyKeyboardMarkup(
        [
            [Buttons.SEARCH_BY_CARD, Buttons.SEARCH_BY_PHONE],
            [Buttons.SEARCH_BY_NAME,Buttons.SEARCH_BY_ID],
            [Buttons.BACK_TO_CUSTOMERS]
        ],
        resize_keyboard=True
    )