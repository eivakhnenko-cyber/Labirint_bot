"""
Конфигурация всех текстов кнопок
Все тексты должны совпадать с текстами в клавиатурах
"""

class Buttons:
    """Тексты кнопок"""
    
    # Главное меню
    INVENTORY = "📦 Инвентаризация"
    REMINDERS = "⏰ Напоминания"
    CUSTOMERS = "👥 Клиенты"
    BONUS_SYSTEM = "🎁 Бонусная система"
    ADMINISTRATION = "⚙️ Администрирование"
    TOOLS = "🔧 Инструменты"
    EXIT = "🚪 Выход"
    BACK_TO_MAIN = "🔙 Назад в главное меню"
    
    # Инвентаризация
    INVENTORY_LIST = "📋 Список товаров"
    CREATE_LIST = "📝 Создать список"
    ADD_ITEM = "➕ Добавить товар"
    COMPARE_INVENTORY = "🔍 Сверить остатки"
    CLEAR_INVENTORY = "🔄 Сбросить список"
    CONFIRM_INVENTORY = "✅ Подтвердить инвентаризацию"
    BACK_TO_INVENTORY = "🔙 Назад в Инвентаризацию"

    CATALOG = "📁 Управление справочником"
    SELECT_CATALOG = "📋 Выбрать из справочника"
    ADD_ARM_CATALOG = "✏️ Ввести вручную"
    ADD_CATALOG = "➕ Добавить в справочник" 
    EDIT_CATEGORY = "🔄 Изменить категорию"
    OTHER_CATEGORY = "📁 Другие категории"
    VIEW_CATALOG = "📋 Просмотр справочника"
    EDIT_CATALOG = "✏️ Редактировать товар" 
    DEL_ITEM_CATALOG = "🗑️ Удалить из справочника"
    BACK_TO_CATALOG = "🔙 Назад в справочник"

    # Напоминания
    REMINDERS_STATUS = "📊 Текущий статус напоминаний"
    SETUP_SCHEDULE = "📅 Настроить расписание"
    SETUP_TYPE = "📝 Настроить тип"
    START_REMINDERS = "🔔 Включить напоминания"
    STOP_REMINDERS = "🔕 Выключить напоминания"
    CHECK_JOBS = "📋 Проверить задания"
    RELOAD_JOBS = "🔄 Перезагрузить задания"
    CHECK_REST = "📦 Проверить остатки"
    START_INVENT = "🔄 Начать инвентаризацию"
    OWN_VERSION = "➕ Свой вариант"
    BACK_TO_REMIND = "🔙 Назад к напоминаниям"
    BACK = "🔙 Назад"
    
    # Клиенты
    REGISTER_CUSTOMER = "👤 Регистрация клиента"
    CUSTOMERS_LIST = "📋 Список клиентов"
    SEARCH_CUSTOMER = "🔍 Поиск клиента"
    ADD_PURCHASE = "💰 Начислить покупку"
    ACTIVATE_CUSTOMER = "✅ Активация клиента"
    DEACTIVATE_CUSTOMER = "❌ Деактивация клиента"
    CUSTOMER_STATISTICS = "📊 Статистика клиентов"
    CHECK_STATUS = "🎯 Проверить статус"
    GET_MY_BONUS = "🎫 Мои бонусы" 
    GET_MY_LEVEL = "📈 Мой уровень"
    GET_MY_STAT = "🏆 Моя статистика"
    ADD_CUSTOMER_BONUS = "➕ Начислить бонусы"
    DEL_CUSTOMER_BONUS = "➖ Списать бонусы"
    BACK_TO_CUSTOMERS = "🔙 Назад к клиентам"
    BACK_TO_SEARCH_RESULT = "🔙 Назад к результатам поиска"
    BACK_TO_CUSTOMERS_LIST = "🔙 Назад к списку клиентов"
    
    # Бонусная система
    LOYALTY_PROGRAM = "🎁 Программа лояльности"
    LEVELS_SETTINGS = "📊 Настройка уровней"
    PROGRAMS_MANAGEMENT = "⚙️ Управление программами"
    PROMOCODES = "🎫 Промокоды"
    LIST_PROGRAM = "📋 Список программ"
    ADD_PROGRAM = "➕ Создать программу"
    SEARCH_PROGRAM = "🔍 Поиск программы"
    ACTIVATE_PROGRAM = "✅ Активация программы"
    DEACIVATE_PROGRAM = "❌ Деактивация программы"
    ANALITIC_PROGRAM = "📊 Статистика программы"

    LIST_LEVELS = "📋 Список уровней"
    ADD_LEVELS = "➕ Создать уровень"
    EDIT_LEVEL = "✏️ Редактирование уровня"
    STATICS_LEVELS = "📈 Статистика по уровням"
    DELETE_LEVELS = "🗑️ Удалить уровень"
    CONFIRM_DEL_LEV_YES = "✅ Да, удалить"
    CONFIRM_DEL_LEV_NO = "❌ Нет, отменить"
    
    PROMO_LIST = "📋 Список промокодов"
    PROMO_ADD = "➕ Создать промокод"
    PROMO_ACTIVATE = "🎯 Активировать промокод"
    PROMO_STAT = "📊 Статистика промокодов"

    BACK_TO_BONUS = "🔙 Назад к бонусной системе"
    
    # Администрирование
    USER_MANAGEMENT = "👥 Управление пользователями"
    ROLE_MANAGEMENT = "🎭 Управление ролями"
    SYSTEM_SETTINGS = "⚙️ Общие настройки"
    SYSTEM_STATS = "📊 Статистика системы"
    FEATURES_MANAGEMENT = "⚡ Функции системы"
    CHAT_MANAGEMENT = "💬 Управление чатом"
    BOT_SETTINGS = "📱 Настройки бота"
    NOTIFICATIONS = "🔔 Уведомления"
    ACTIVATE_FUNC = "✅ Активировать функцию"
    DEACIVEATE_FUNC = "❌ Деактивировать функцию"
    STATS_FUNC = "📊 Статус функций"

    #Управление пользователями
    PROFILE = "👤 Профиль"
    ALL_USERS = "📋 Список пользователей"
    ADD_USER = "👤 Добавить пользователя"
    EDIT_USER = "✏️ Изменить пользователя"
    DELL_USER = "🗑️ Удалить пользователя"
    ALL_ROLS = "📋 Список ролей"
    SET_ROLS = "🎯 Назначение ролей"
    CREATE_ROLS = "➕ Создать роль" 
    EDIT_ROLS = "✏️ Изменить роль"

    # Профиль
    PROFILE_INFO = "ℹ️ Информация о профиле"
    CHANGE_ROLE = "🔧 Сменить свою роль"
    
    BACK_TO_ADMIN = "🔙 Назад к администрированию"
    BACK_TO_SETTINGS = "🔙 Назад к настройкам"
    
    # Управление чатом
    CLEANUP_CHAT = "🗑️ Очистить чат"
    CLEANUP_ALL = "🗑️ Удалить все сообщения"
    CLEANUP_OWN = "👤 Удалить только свои сообщения"
    CLEANUP_COUNT = "🔢 Удалить XX сообщений"
    BACK_TO_CHAT = "🔙 Назад к управлению чатом"
    
    
    
    # Общие
    CANCEL = "❌ Отмена"
    EDIT_USER_CANCEL = "❌ Отмена"
    EDIT_USER_CONFIRM = "✅ Подтвердить"
    CONFIRM_YES = "✅ Да"
    CONFIRM_NO = "❌ Нет"
    CONFIRM_DEL_YES = "✅ Да, Удалить"
    CONFIRM_DEL_NO = "❌ Нет, Отменить"

    # Поиск клиента
    SEARCH_BY_CARD = "💳 Поиск по карте"
    SEARCH_BY_PHONE = "📱 Поиск по телефону"
    SEARCH_BY_NAME = "👤 Поиск по имени"
    SEARCH_BY_ID = "🆔 Поиск по ID"
    PURCHASE_HISTORY = "📊 История покупок"
    NEW_SEARCH = "🔍 Новый поиск"

    REPORT = "📊 Отчеты"
    START_WATCH = "🔔 Открыть смену"
    STOP_WATCH = "🔕 Закрыть смену"
    REPORT_HISTORY = "📊 История отчетов"

# Словарь для быстрого доступа
BUTTONS_DICT = {attr: value for attr, value in vars(Buttons).items() 
                if not attr.startswith('_')}