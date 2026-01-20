# handlers/admin.py
import logging
from telegram import Update
from telegram.ext import CallbackContext
from typing import Dict
from handlers.admin_roles_class import role_manager, UserRole, Permission
from handlers.admin_users_class import users_manager
from handlers.admin_edit_user_flow import edit_user_conversation_handler

from keyboards.global_keyb import get_main_keyboard
from keyboards.admin_keyb import get_admin_keyboard, EditUserStep, get_user_management_keyboard, get_role_management_keyboard, get_chat_management_keyboard, get_features_management_keyboard, get_system_settings_keyboard

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: CallbackContext) -> None:
    """Панель администратора"""
    try:
        user_id = update.effective_user.id
        
        # Проверяем права
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text(
                "❌ У вас нет прав для доступа к панели администратора.",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
        
        message = "⚙️ Панель администратора\n\n"
        message += "Доступные функции:\n"
        message += "• 👥 Управление пользователями\n"
        message += "• ⚙️ Управление ролями\n"
        message += "• 📊 Статистика системы\n"
        message += "• 🔧 Настройки системы"
        
        await update.message.reply_text(
            message,
            reply_markup=await get_admin_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в admin_panel: {e}")
        await update.message.reply_text(
            "Ошибка загрузки панели администратора.",
            reply_markup=await get_main_keyboard(user_id)
        )

async def manage_users(update: Update, context: CallbackContext) -> None:
    """Управление пользователями"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text("❌ Нет прав")
            return
        
        # Получаем список пользователей
        users = await users_manager.get_all_users()
        
        if not users:
            await update.message.reply_text("📭 В системе нет пользователей.")
            return
        
        message = "👥 Список пользователей:\n\n"
        for i, user in enumerate(users, 1):
            message += f"{i}. ID: {user['user_id']}\n"
            message += f"   Роль: {user['role_name']}\n"
            message += f"   Зарегистрирован: {user['created_at'][:10]}\n\n"
        
        message += "Используйте команду /setrole <user_id> <role> для изменения роли."
        
        await update.message.reply_text(message[:4000])  # Ограничение Telegram
        
    except Exception as e:
        logger.error(f"Ошибка в manage_users: {e}")
        await update.message.reply_text("Ошибка загрузки списка пользователей.")

async def admin_main_menu(update: Update, context: CallbackContext) -> None:
    """Главное меню администрирования"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if role != UserRole.ADMIN:
        await update.message.reply_text(
            "⛔ Доступно только для администраторов.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    await update.message.reply_text(
        "⚙️ *Администрирование*\n\n"
        "Выберите раздел для управления:",
        reply_markup=await get_admin_keyboard(),
        parse_mode='Markdown'
    )

# ============================================================================
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# ============================================================================

async def manage_users_menu(update: Update, context: CallbackContext) -> None:
    """Меню управления пользователями"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text(
                "❌ У вас нет прав для управления пользователями.",
                reply_markup=await get_admin_keyboard()
            )
            return
        
        message = "👥 *Управление пользователями*\n\n"
        message += "*Доступные действия:*\n"
        message += "• 📋 Список пользователей\n"
        message += "• 👤 Добавить пользователя\n"
        message += "• ✏️ Изменить пользователя\n"
        message += "• 🗑️ Удалить пользователя"
        
        await update.message.reply_text(
            message,
            reply_markup=await get_user_management_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в manage_users_menu: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки меню управления пользователями.",
            reply_markup=await get_admin_keyboard()
        )

async def show_all_users(update: Update, context: CallbackContext) -> None:
    """Показать список всех пользователей (без посетителей)"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text("❌ У вас нет прав для просмотра списка пользователей.")
            return
        
        # Получаем список пользователей без посетителей
        # Сначала попробуем использовать метод get_users_without_visitors
        try:
            users = await users_manager.get_users_without_visitors()
        except AttributeError:
            # Если метод не существует, используем общий метод и фильтруем
            all_users = await users_manager.get_all_users()
            users = [u for u in all_users if u.get('role') != UserRole.VISITOR.value]
        
        if not users:
            await update.message.reply_text(
                "📭 В системе нет пользователей (кроме посетителей).",
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        message = "👥 *Список пользователей:*\n\n"
        for i, user in enumerate(users, 1):
            message += f"*{i}. ID:* `{user.get('user_id', 'N/A')}`\n"
            message += f"   *Роль:* {user.get('role_name', 'Неизвестно')}\n"
            
            # Добавляем дополнительную информацию, если она есть
            if user.get('username'):
                message += f"   *Username:* @{user['username']}\n"
            if user.get('first_name') or user.get('last_name'):
                name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                message += f"   *Имя:* {name if name else 'Не указано'}\n"
            
            if user.get('created_at'):
                message += f"   *Дата регистрации:* {user['created_at'][:10]}\n"
            
            message += "\n"
        
        await update.message.reply_text(
            message[:4000],
            reply_markup=await get_user_management_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_all_users: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки списка пользователей.",
            reply_markup=await get_user_management_keyboard()
        )

async def add_user_command(update: Update, context: CallbackContext) -> None:
    """Команда для добавления пользователя"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text("❌ У вас нет прав для добавления пользователей.")
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "Использование: `/adduser <user_id> [role]`\n\n"
                "Примеры:\n"
                "• `/adduser 123456` - добавить с ролью бариста (по умолчанию)\n"
                "• `/adduser 123456 admin` - добавить как администратора\n"
                "• `/adduser 123456 manager` - добавить как менеджера\n\n"
                "Роли: admin, manager, barista",
                parse_mode='Markdown',
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        target_user_id = int(context.args[0])
        
        # Определяем роль (по умолчанию - BARISTA)
        role_str = context.args[1].lower() if len(context.args) > 1 else "barista"
        
        role_map = {
            'admin': UserRole.ADMIN,
            'manager': UserRole.MANAGER,
            'barista': UserRole.BARISTA,
        }
        
        if role_str not in role_map:
            await update.message.reply_text(
                "❌ Неверная роль. Допустимые значения: admin, manager, barista",
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        new_role = role_map[role_str]
        
        # 1. Проверяем, существует ли пользователь в таблице user_roles
        existing_role = await role_manager.get_user_role(target_user_id)
        
        # 2. Проверяем, есть ли запись в таблице users
        user_exists_in_users = await users_manager.check_user_in_users_table(target_user_id)

        # Проверяем, существует ли пользователь уже
        if existing_role:
            if existing_role == UserRole.GUEST or existing_role == UserRole.VISITOR:
                if not user_exists_in_users:
                    await users_manager.add_user_to_users_table(target_user_id)
                   
                # Обновляем роль
                success = await role_manager.set_user_role(target_user_id, new_role)
                
                if success:
                    role_name = role_manager.get_role_name(new_role)
                    await update.message.reply_text(
                        f"✅ Пользователь `{target_user_id}` успешно добавлен в систему с ролью *{role_name}*\n"
                        f"*Предыдущая роль:* {role_manager.get_role_name(existing_role)}",
                        parse_mode='Markdown',
                        reply_markup=await get_user_management_keyboard()
                    )
                else:
                    await update.message.reply_text(
                       "❌ Не удалось обновить роль пользователя.",
                        reply_markup=await get_user_management_keyboard()
                    )
            else:
                # Пользователь уже имеет рабочую роль (admin, manager, barista)
                current_role_name = role_manager.get_role_name(existing_role)
                new_role_name = role_manager.get_role_name(new_role)
                
                await update.message.reply_text(
                    f"⚠️ Пользователь `{target_user_id}` уже существует в системе.\n\n"
                    f"*Текущая роль:* {current_role_name}\n"
                    f"*Запрашиваемая роль:* {new_role_name}\n\n"
                    "Для изменения роли используйте команду:\n"
                    f"`/setrole {target_user_id} {role_str}`",
                    parse_mode='Markdown',
                    reply_markup=await get_user_management_keyboard()
                )
            return
        
        # 3. Если пользователя нет в user_roles вообще (новый пользователь)
        # Добавляем в таблицу users
        if not user_exists_in_users:
            await users_manager.add_user_to_users_table(target_user_id)
        
        # Устанавливаем роль
        success = await role_manager.set_user_role(target_user_id, new_role)
        
        if success:
            role_name = role_manager.get_role_name(new_role)
            await update.message.reply_text(
                f"✅ Пользователь `{target_user_id}` успешно добавлен в систему с ролью *{role_name}*",
                parse_mode='Markdown',
                reply_markup=await get_user_management_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось добавить пользователя.",
                reply_markup=await get_user_management_keyboard()
            )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат user_id. Введите число.",
            reply_markup=await get_user_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в add_user_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка добавления пользователя.",
            reply_markup=await get_user_management_keyboard()
        )

async def edit_user_command(update: Update, context: CallbackContext) -> None:
    """Команда для редактирования пользователя"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text("❌ У вас нет прав для редактирования пользователей.")
            return
        
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "Использование: `/edituser <user_id> <field> <value>`\n\n"
                "*Примеры:*\n"
                "• `/edituser 123456 username new_username`\n"
                "• `/edituser 123456 first_name Иван`\n"
                "• `/edituser 123456 last_name Иванов`\n"
                "• `/edituser 123456 phone_numb +79991234567`\n\n"
                "*Доступные поля:* username, first_name, last_name, phone_numb",
                parse_mode='Markdown',
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        target_user_id = int(context.args[0])
        field = context.args[1].lower()
        value = ' '.join(context.args[2:])
        
        # Проверяем, существует ли пользователь
        try:
            existing_role = await role_manager.get_user_role(target_user_id)
            if not existing_role:
                await update.message.reply_text(
                    f"❌ Пользователь {target_user_id} не найден в системе.",
                    reply_markup=await get_user_management_keyboard()
                )
                return
        except:
            await update.message.reply_text(
                f"❌ Пользователь {target_user_id} не найден в системе.",
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        # Определяем доступные поля
        allowed_fields = ['username', 'first_name', 'last_name', 'phone_numb']
        
        if field not in allowed_fields:
            await update.message.reply_text(
                f"❌ Неверное поле. Допустимые значения: {', '.join(allowed_fields)}",
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        # Обновляем информацию о пользователе
        try:
            # Используем метод update_user_info
            success = await users_manager.update_user_info(target_user_id, **{field: value})

            if success:
                await update.message.reply_text(
                    f"✅ Поле {field} пользователя {target_user_id} успешно обновлено на: {value}",
                    reply_markup=await get_user_management_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ Не удалось обновить поле {field} для пользователя {target_user_id}.",
                    reply_markup=await get_user_management_keyboard()
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат user_id. Введите число.",
                reply_markup=await get_user_management_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка в edit_user_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка редактирования пользователя.",
            reply_markup=await get_user_management_keyboard()
        )

async def delete_user_command(update: Update, context: CallbackContext) -> None:
    """Команда для удаления пользователя"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text("❌ У вас нет прав для удаления пользователей.")
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "Использование: `/deluser <user_id>`\n\n"
                "Пример: `/deluser 123456`\n\n"
                "*Внимание:* Это действие нельзя отменить!",
                parse_mode='Markdown',
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        target_user_id = int(context.args[0])
        
        # Проверяем, не пытаемся ли удалить себя
        if user_id == target_user_id:
            await update.message.reply_text(
                "❌ Вы не можете удалить себя.",
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        # Проверяем, существует ли пользователь
        try:
            existing_role = await role_manager.get_user_role(target_user_id)
            if not existing_role:
                await update.message.reply_text(
                    f"❌ Пользователь {target_user_id} не найден в системе.",
                    reply_markup=await get_user_management_keyboard()
                )
                return
            
            # Проверяем, не пытаемся ли удалить последнего администратора
            if existing_role == UserRole.ADMIN:
                # Получаем всех пользователей
                all_users = await users_manager.get_all_users()
                admin_count = sum(1 for u in all_users if u.get('role') == UserRole.ADMIN.value)
                
                if admin_count <= 1:
                    await update.message.reply_text(
                        "❌ Нельзя удалить последнего администратора в системе.",
                        reply_markup=await get_user_management_keyboard()
                    )
                    return
        except:
            await update.message.reply_text(
                f"❌ Пользователь {target_user_id} не найден в системе.",
                reply_markup=await get_user_management_keyboard()
            )
            return
        
        # Удаляем пользователя
        try:
            # Используем метод delete_user
            success = await users_manager.delete_user(user_id, target_user_id)
            
            if success:
                await update.message.reply_text(
                    f"✅ Пользователь `{target_user_id}` успешно удален из системы.",
                    parse_mode='Markdown',
                    reply_markup=await get_user_management_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ Не удалось удалить пользователя {target_user_id}.",
                    reply_markup=await get_user_management_keyboard()
                )
                
        except Exception as db_error:
                logger.error(f"Ошибка БД при удалении пользователя: {db_error}")
                await update.message.reply_text(
                    "❌ Ошибка удаления пользователя из базы данных.",
                    reply_markup=await get_user_management_keyboard()
                )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат user_id. Введите число.",
            reply_markup=await get_user_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в delete_user_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка удаления пользователя.",
            reply_markup=await get_user_management_keyboard()
        )


# ============================================================================
# СИСТЕМНЫЕ ФУНКЦИИ
# ============================================================================

async def system_stats(update: Update, context: CallbackContext) -> None:
    """Статистика системы"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_USERS):
            await update.message.reply_text(
                "❌ У вас нет прав для просмотра статистики.",
                reply_markup=await get_admin_keyboard()
            )
            return
        
        users = await users_manager.get_all_users()
        
        # Считаем статистику по ролям
        role_stats = {}
        for user in users:
            role = user.get('role')
            if role:
                role_stats[role] = role_stats.get(role, 0) + 1
        
        message = "📊 *Статистика системы*\n\n"
        message += f"*Всего пользователей:* {len(users)}\n\n"
        
        if role_stats:
            message += "*Распределение по ролям:*\n"
            for role, count in role_stats.items():
                try:
                    role_name = role_manager.get_role_name(UserRole(role))
                    percentage = (count / len(users)) * 100 if len(users) > 0 else 0
                    message += f"• {role_name}: {count} ({percentage:.1f}%)\n"
                except:
                    message += f"• {role}: {count}\n"
        else:
            message += "Нет данных о распределении по ролям\n"
        
        # Дополнительная статистика
        message += "\n*Дополнительная информация:*\n"
        
        # Считаем пользователей без посетителей
        try:
            non_visitors = await users_manager.get_users_without_visitors()
            message += f"• Активных пользователей (без посетителей): {len(non_visitors)}\n"
        except:
            pass
        
        # Статистика по ролям с деталями
        message += "\n*Детали по ролям:*\n"
        for role in UserRole:
            count = role_stats.get(role.value, 0)
            if count > 0:
                role_name = role_manager.get_role_name(role)
                message += f"• {role_name}: {count}\n"
        
        await update.message.reply_text(
            message[:4000],
            reply_markup=await get_admin_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в system_stats: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки статистики.",
            reply_markup=await get_main_keyboard(user_id)
        )

async def system_settings(update: Update, context: CallbackContext) -> None:
    """Общие настройки системы"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_SYSTEM):
            await update.message.reply_text(
                "❌ У вас нет прав для доступа к настройкам системы.",
                reply_markup=await get_admin_keyboard()
            )
            return
        
        message = "⚙️ *Общие настройки системы*\n\n"
        message += "*Доступные разделы:*\n"
        message += "• ⚡ Функции системы\n"
        message += "• 💬 Управление чатом\n"
        message += "• 📱 Настройки бота\n"
        message += "• 🔔 Уведомления\n\n"
        message += "Выберите раздел для настройки:"
        
        await update.message.reply_text(
            message,
            reply_markup=await get_system_settings_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в system_settings: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки настроек системы.",
            reply_markup=await get_admin_keyboard()
        )

# ============================================================================
# ПРОФИЛЬ И ИНФОРМАЦИЯ
# ============================================================================

async def my_role(update: Update, context: CallbackContext) -> None:
    """Показывает текущую роль пользователя"""
    try:
        user_id = update.effective_user.id
        user_info = await get_user_info(user_id)
        
        message = f"👤 *Ваш профиль*\n\n"
        message += f"*ID:* `{user_info['user_id']}`\n"
        message += f"*Роль:* {user_info['role_name']}\n"
        message += f"*Доступных функций:* {user_info['permission_count']}\n\n"
        
        if user_info.get('permissions'):
            message += "*Доступные функции:*\n"
            
            # Группируем разрешения по категориям
            categories = {
                'Инвентаризация': ['view_inventory', 'manage_inventory', 'confirm_inventory'],
                'Напоминания': ['view_reminders', 'manage_reminders'],
                'Управление': ['manage_users', 'manage_roles', 'manage_customers'],
                'Отчеты': ['view_reports', 'manage_reports', 'cleanup_chat'],
                'Бонусы': ['view_bonuses', 'manage_bonuses'],
                'Профиль': ['view_profile']
            }
            
            for category, perms in categories.items():
                user_perms_in_category = [p for p in user_info['permissions'] if p in perms]
                if user_perms_in_category:
                    message += f"\n*{category}:*\n"
                    for perm in user_perms_in_category:
                        func_name = perm.replace('_', ' ').title()
                        message += f"• {func_name}\n"
        else:
            message += "Нет информации о доступных функциях.\n"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=await get_main_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в my_role: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки профиля.",
            reply_markup=await get_main_keyboard(user_id)
        )

async def make_admin(update: Update, context: CallbackContext) -> None:
    """Сделать пользователя администратором (команда для разработки)"""
    try:
        user_id = update.effective_user.id
        
        # Получаем всех пользователей
        users = await users_manager.get_all_users()
        
        if not users:
            # Первый пользователь становится администратором
            await role_manager.set_user_role(user_id, UserRole.ADMIN)
            await update.message.reply_text(
                "🎉 Вы стали первым администратором системы!",
                reply_markup=await get_admin_keyboard()
            )
        else:
            # Проверяем, есть ли уже админы
            admins = [u for u in users if u.get('role') == 'admin']
            if not admins:
                await role_manager.set_user_role(user_id, UserRole.ADMIN)
                await update.message.reply_text(
                    "✅ Вы назначены администратором!",
                    reply_markup=await get_admin_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ В системе уже есть {len(admins)} администратор(ов).\n"
                    f"Для назначения используйте команду `/setrole` от существующего администратора.",
                    parse_mode='Markdown',
                    reply_markup=await get_main_keyboard(user_id)
                )
                
    except Exception as e:
        logger.error(f"Ошибка в make_admin: {e}")
        await update.message.reply_text(
            "❌ Ошибка назначения администратора.",
            reply_markup=await get_main_keyboard(update.effective_user.id)
        )

async def back_to_main(update: Update, context: CallbackContext) -> None:
    """Возврат в главное меню"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🔙 Возврат в главное меню",
        reply_markup=await get_main_keyboard(user_id)
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Показывает список доступных команд"""
    commands = [
        "/admin - Панель администратора",
        "/users - Управление пользователями",
        "/adduser <id> [role] - Добавить пользователя",
        "/edituser <id> <field> <value> - Редактировать пользователя",
        "/deluser <id> - Удалить пользователя",
        "/myrole - Показать свою роль",
    ]
    
    await update.message.reply_text(
        "📋 *Доступные команды:*\n\n" + "\n".join(commands),
        parse_mode='Markdown'
    )

async def get_user_info(user_id: int) -> Dict:
        """Получает информацию о пользователе"""

        role = await role_manager.get_user_role(user_id)
        permissions = role_manager.get_role_permissions(role)
        
        return {
            'user_id': user_id,
            'role': role,
            'role_name': role_manager.get_role_name(role),
            'permissions': [p.value for p in permissions],
            'permission_count': len(permissions)
        }