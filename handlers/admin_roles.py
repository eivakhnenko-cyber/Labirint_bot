# handlers/admin.py
import logging
from telegram import Update
from telegram.ext import CallbackContext
from enum import Enum
from typing import Dict, List, Optional
from handlers.admin_roles_class import role_manager, UserRole, Permission
from keyboards.global_keyb import get_main_keyboard
from keyboards.admin_keyb import get_admin_keyboard, get_role_management_keyboard

logger = logging.getLogger(__name__)

# ============================================================================
# УПРАВЛЕНИЕ РОЛЯМИ
# ============================================================================

async def manage_roles_menu(update: Update, context: CallbackContext) -> None:
    """Меню управления ролями"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_ROLES):
            await update.message.reply_text(
                "❌ У вас нет прав для управления ролями.",
                reply_markup=await get_admin_keyboard()
            )
            return
        
        message = "🎭 *Управление ролями*\n\n"
        message += "*Доступные действия:*\n"
        message += "• 📋 Список ролей\n"
        message += "• 🎯 Назначение ролей\n"
        message += "• ➕ Создать роль\n"
        message += "• ✏️ Изменить роль"
        
        await update.message.reply_text(
            message,
            reply_markup=await get_role_management_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в manage_roles_menu: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки меню управления ролями.",
            reply_markup=await get_admin_keyboard()
        )

async def show_all_roles(update: Update, context: CallbackContext) -> None:
    """Показать список всех ролей"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_ROLES):
            await update.message.reply_text("❌ У вас нет прав для просмотра списка ролей.")
            return
        
        message = "🎭 *Список ролей в системе:*\n\n"
        
        # Получаем информацию о всех ролях
        try:
            roles_info = role_manager.get_all_roles_info()
            
            for role_info in roles_info:
                role_name = role_info.get('role_name', role_info.get('role', 'Неизвестно'))
                permissions_count = role_info.get('permission_count', 0)
                
                # Используем экранирование для безопасного форматирования
                #safe_role_name = role_name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
                #message += f"*{safe_role_name}* ({role_info.get('role', 'N/A')})\n"

                # Экранируем спецсимволы для MarkdownV2
                safe_role_name = role_manager.escape_markdown_v2(role_name)
                safe_role_value = role_manager.escape_markdown_v2(role_info.get('role', 'N/A'))
                
                message += f"*{safe_role_name}* \\({safe_role_value}\\)\n"
                message += f"  • Доступных функций: {permissions_count}\n"
                
                # Добавляем информацию о разрешениях, если они есть
                if role_info.get('permissions'):
                    message += f"  • Ключевые функции: "
                    key_perms = role_info['permissions'][:3]  # Показываем только первые 3
                    # Экранируем названия разрешений
                    #safe_perms = [p.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`') for p in key_perms]
                    safe_perms = [role_manager.escape_markdown_v2(p) for p in key_perms]
                    message += ', '.join(safe_perms)

                    if len(role_info['permissions']) > 3:
                        message += f" и ещё {len(role_info['permissions']) - 3}"
                    message += "\n"
                
                message += "\n"
                
        except AttributeError:
            # Если метод не существует, показываем базовую информацию
            for role in UserRole:
                role_name = role_manager.get_role_name(role)
                permissions = role_manager.get_role_permissions(role)
                
                # Экранируем спецсимволы в названии роли
                #safe_role_name = role_name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
                #message += f"*{safe_role_name}* ({role.value})\n"
                safe_role_name = role_manager.escape_markdown_v2(role_name)
                safe_role_value = role_manager.escape_markdown_v2(role.value)
                
                message += f"*{safe_role_name}* \\({safe_role_value}\\)\n"
                message += f"  • Доступных функций: {len(permissions)}\n"
                
                # Показываем ключевые разрешения
                if permissions:
                    key_perms = [p.value for p in permissions[:3]]
                     # Экранируем названия разрешений
                    #safe_perms = [p.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`') for p in key_perms]
                    safe_perms = [role_manager.escape_markdown_v2(p) for p in key_perms]
                    message += f"  • Ключевые функции: {', '.join(safe_perms)}"
                    if len(permissions) > 3:
                        message += f" и ещё {len(permissions) - 3}"
                    message += "\n"
                
                message += "\n"
        
        message += "\n*Использование:*\n"
        usage_text = role_manager.escape_markdown_v2(
            "• Для изменения роли используйте команду `/setrole <user_id> <role>`\n"
            "• Доступные роли: admin, manager, barista, visitor, guest"
        )

        # Ограничиваем длину сообщения и проверяем форматирование
        if len(message) > 4000:
            message = message[:3997] + "..."
        
        await update.message.reply_text(
            message,
            reply_markup=await get_role_management_keyboard(),
            parse_mode='MarkdownV2'  # Используем MarkdownV2 для лучшей совместимости
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_all_roles: {e}")
        # Альтернативный вариант без Markdown при ошибке
        try:
            # Простой текст без форматирования
            simple_message = "🎭 Список ролей в системе:\n\n"
            
            for role in UserRole:
                role_name = role_manager.get_role_name(role)
                permissions = role_manager.get_role_permissions(role)
                
                simple_message += f"{role_name} ({role.value})\n"
                simple_message += f"  • Доступных функций: {len(permissions)}\n"
                
                if permissions:
                    key_perms = [p.value.replace('_', ' ') for p in permissions[:2]]
                    simple_message += f"  • Пример: {', '.join(key_perms)}\n"
                
                simple_message += "\n"
            
            simple_message += "\nИспользование:\n"
            simple_message += "• Для изменения роли: /setrole <user_id> <role>\n"
            simple_message += "• Доступные роли: admin, manager, barista, visitor, guest"
            
            await update.message.reply_text(
                simple_message[:4000],
                reply_markup=await get_role_management_keyboard()
            )
        except Exception as e2:
            logger.error(f"Ошибка в альтернативном выводе: {e2}")
            await update.message.reply_text(
                "❌ Ошибка загрузки списка ролей. Пожалуйста, попробуйте позже.",
                reply_markup=await get_role_management_keyboard()
            )

async def set_user_role_command(update: Update, context: CallbackContext) -> None:
    """Команда для установки роли пользователю"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_ROLES):
            await update.message.reply_text(
                "❌ У вас нет прав для изменения ролей.",
                reply_markup=await get_role_management_keyboard()
            )
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Использование: `/setrole <user_id> <role>`\n\n"
                "*Примеры:*\n"
                "• `/setrole 123456 admin`\n"
                "• `/setrole 123456 manager`\n"
                "• `/setrole 123456 barista`\n"
                "• `/setrole 123456 visitor`\n\n"
                "*Доступные роли:* admin, manager, barista, visitor, guest",
                parse_mode='Markdown',
                reply_markup=await get_role_management_keyboard()
            )
            return
        
        target_user_id = int(context.args[0])
        role_str = context.args[1].lower()
        
        # Проверяем, не пытаемся ли изменить роль самому себе
        if user_id == target_user_id:
            await update.message.reply_text(
                "⚠️ Вы не можете изменить свою собственную роль.",
                reply_markup=await get_role_management_keyboard()
            )
            return
        
        # Парсим роль
        role_map = {
            'admin': UserRole.ADMIN,
            'manager': UserRole.MANAGER,
            'barista': UserRole.BARISTA,
            'visitor': UserRole.VISITOR,
            'guest': UserRole.GUEST,
        }
        
        if role_str not in role_map:
            await update.message.reply_text(
                "❌ Неверная роль. Допустимые значения: admin, manager, barista, visitor, guest",
                reply_markup=await get_role_management_keyboard()
            )
            return
        
        new_role = role_map[role_str]
        
        # Меняем роль
        success = await role_manager.change_user_role(user_id, target_user_id, new_role)
        
        if success:
            role_name = role_manager.get_role_name(new_role)
            await update.message.reply_text(
                f"✅ Роль пользователя `{target_user_id}` изменена на *{role_name}*",
                parse_mode='Markdown',
                reply_markup=await get_role_management_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось изменить роль.\n"
                "Возможные причины:\n"
                "• У вас недостаточно прав\n"
                "• Пользователь не найден\n"
                "• Попытка изменить роль последнего администратора",
                reply_markup=await get_role_management_keyboard()
            )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат user_id. Введите число.",
            reply_markup=await get_role_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в set_user_role_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка изменения роли.",
            reply_markup=await get_role_management_keyboard()
        )

async def create_role_command(update: Update, context: CallbackContext) -> None:
    """Команда для создания новой роли (заглушка)"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_ROLES):
            await update.message.reply_text("❌ У вас нет прав для создания ролей.")
            return
        
        await update.message.reply_text(
            "⚠️ *Создание новых ролей*\n\n"
            "В текущей версии системы создание новых ролей не поддерживается.\n"
            "Система использует фиксированный набор из 4 ролей:\n\n"
            "1. 👑 *Администратор* - полный доступ\n"
            "2. 👔 *Менеджер* - почти полный доступ\n"
            "3. ☕ *Бариста* - ограниченный доступ\n"
            "4. 👤 *Посетитель* - минимальные права\n"
            "5. 👤 *Гость* - только просмотр профиля\n\n"
            "Для изменения прав существующих ролей обратитесь к разработчику.",
            parse_mode='Markdown',
            reply_markup=await get_role_management_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в create_role_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка обработки запроса.",
            reply_markup=await get_role_management_keyboard()
        )

async def edit_role_command(update: Update, context: CallbackContext) -> None:
    """Команда для редактирования роли (заглушка)"""
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.MANAGE_ROLES):
            await update.message.reply_text("❌ У вас нет прав для редактирования ролей.")
            return
        
        await update.message.reply_text(
            "⚠️ *Редактирование ролей*\n\n"
            "В текущей версии системы редактирование прав ролей не поддерживается через интерфейс.\n\n"
            "*Доступные действия:*\n"
            "• Просмотр списка ролей - команда `/roles`\n"
            "• Изменение роли пользователя - команда `/setrole <id> <role>`\n\n"
            "Для изменения набора прав существующих ролей обратитесь к разработчику.",
            parse_mode='Markdown',
            reply_markup=await get_role_management_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в edit_role_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка обработки запроса.",
            reply_markup=await get_role_management_keyboard()
        )