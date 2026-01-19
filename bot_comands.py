# bot_commands.py
from telegram import BotCommand, BotCommandScopeChat
from handlers.admin_roles_class import role_manager, UserRole, Permission
# Определяем список команд для меню бота
BOT_COMMANDS = [
    BotCommand("start", "🚀 Запустить бота"),
    BotCommand("role", "🎭 Моя роль"),
]

# Команды для администраторов (дополнительно)
ADMIN_COMMANDS = [
    BotCommand("users", "👥 Управление пользователями"),
    BotCommand("stats", "📊 Статистика системы"),
    BotCommand("makeadmin", "👑 Назначить администратора"),
    BotCommand("adduser", "➕ Добавить пользователя"),
    BotCommand("edituser", "✏️ Редактировать пользователя"),
    BotCommand("deluser", "🗑️ Удалить пользователя"),
    BotCommand("setrole", "🎯 Назначить роль"),
    BotCommand("admin_panel", "⚙️ Панель администратора"),
    BotCommand("manage_catalog", "📁 Управление каталогом"),
    BotCommand("manage_reminders", "⏰ Управление напоминаниями"),
    BotCommand("system_stats", "📈 Подробная статистика"),
]

# Команды для менеджеров/сотрудников
USER_COMMANDS = [
    BotCommand("inventory_menu", "📦 Инвентаризация"),
    BotCommand("customers_menu", "👥 Клиенты"),
    BotCommand("bonus_menu", "🎁 Бонусы"),
    BotCommand("cleanup_menu", "🧹 Очистка"),
    BotCommand("reminders_menu", "⏰ Напоминания"),
    BotCommand("profile_menu", "👤 Профиль"),
]

USER_VISITOR = [
    BotCommand("bonus_menu", "🎁 Бонусы"),
    BotCommand("profile_menu", "👤 Профиль"),
]

USER_GUEST = [
    BotCommand("profile_menu", "👤 Профиль"),
]

async def set_default_commands(application):
    """Установка команд по умолчанию для всех пользователей"""
    await application.bot.set_my_commands(BOT_COMMANDS)
    print("✅ Меню команд установлено")

async def set_user_commands(update, context):
    """Установка команд для конкретного пользователя в зависимости от роли"""

    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    # Базовые команды для всех
    commands = BOT_COMMANDS.copy()
    
    # Добавляем команды в зависимости от роли
    if role == UserRole.ADMIN:
        commands.extend(ADMIN_COMMANDS)
        commands.extend(USER_COMMANDS)
    elif role == UserRole.VISITOR:
        commands.extend(USER_VISITOR)
    elif role == UserRole.GUEST:  
        commands.extend(USER_GUEST)
    
    # Устанавливаем команды
    await context.bot.set_my_commands(
        commands,
        scope=BotCommandScopeChat(chat_id=user_id)
    )