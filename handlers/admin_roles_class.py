# handlers/roles.py
import logging
from typing import Dict, List, Optional
from enum import Enum
from database import sqlite_connection

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """Система ролей пользователей. Всего 4 роли."""
    ADMIN = "admin" # Администратор - полный доступ
    MANAGER = "manager"  # Менеджер - почти полный доступ, кроме управления ролям
    BARISTA = "barista"  # Бариста - ограниченный доступ для операций
    VISITOR = "visitor" # Посетитель - минимальные права, только просмотр своего профиля
    GUEST = "guest" # не зарегистрированный кллиент


class Permission(Enum):
    """Разрешения/функции бота Каждое разрешение соответствует 
    определенной функциональности в системе."""
    
    # === Основные функции инвентаризации ===
    VIEW_INVENTORY = "view_inventory"         # Просмотр инвентаря
    MANAGE_INVENTORY = "manage_inventory"     # Управление инвентарем (добавление/изменение)
    CONFIRM_INVENTORY = "confirm_inventory"   # Подтверждение инвентаризации
    
    # === Функции напоминаний ===
    VIEW_REMINDERS = "view_reminders"         # Просмотр напоминаний
    MANAGE_REMINDERS = "manage_reminders"     # Создание/управление напоминаниями
    
    # === Управление чатом ===
    MANAGE_SYSTEM = "manage_system"
    CLEANUP_CHAT = "cleanup_chat"             # Очистка чата (техническая функция)
    
    # === Отчеты и аналитика ===
    VIEW_REPORTS = "view_reports"             # Просмотр отчетов
    MANAGE_REPORTS = "manage_reports"

    # === Бонусная система ===
    VIEW_BONUSES = "view_bonuses"             # Просмотр бонусной системы
    MANAGE_BONUSES = "manage_bonuses"         # Управление бонусными программами
    
    # === Управление пользователями ===
    MANAGE_USERS = "manage_users"             # Управление пользователями
    MANAGE_ROLES = "manage_roles"             # Управление ролями (только для админа)
    
    # === Управление клиентами ===
    MANAGE_CUSTOMERS = "manage_customers"     # Управление клиентами (регистрация, начисление покупок и т.д.)
    
    # === Профиль пользователя ===
    VIEW_PROFILE = "view_profile"             # Просмотр своего профиля (есть у всех)

class RoleManager:
    """Менеджер ролей и разрешений"""
    # ====================================================================
    # НАСТРОЙКИ РОЛЕЙ И РАЗРЕШЕНИЙ
    # Здесь определяются права для каждой роли в системе.
    # ====================================================================

    ROLE_PERMISSIONS = {
        # === АДМИНИСТРАТОР (admin) ===
        # Полный доступ ко всем функциям системы
        UserRole.ADMIN: [
            # Инвентаризация
            Permission.VIEW_INVENTORY,
            Permission.MANAGE_INVENTORY,
            Permission.CONFIRM_INVENTORY,
            # Напоминания
            Permission.VIEW_REMINDERS,
            Permission.MANAGE_REMINDERS,
            # Управление чатом
            Permission.MANAGE_SYSTEM,
            Permission.CLEANUP_CHAT,
            # Отчеты
            Permission.VIEW_REPORTS,
            Permission.MANAGE_REPORTS,
            # Бонусная система
            Permission.VIEW_BONUSES,
            Permission.MANAGE_BONUSES,
            # Управление пользователями
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            # Управление клиентами
            Permission.MANAGE_CUSTOMERS,
            # Профиль
            Permission.VIEW_PROFILE,
        ],
        # === МЕНЕДЖЕР (manager) ===
        # Может регистрировать посетителей, активировать/деактивировать,
        # проводить и принимать инвентаризацию, просматривать бонусную систему
        UserRole.MANAGER: [
            # Инвентаризация
            Permission.VIEW_INVENTORY,
            Permission.MANAGE_INVENTORY,
            Permission.CONFIRM_INVENTORY,      # Может принимать инвентаризацию
            # Напоминания
            Permission.VIEW_REMINDERS,
            Permission.MANAGE_REMINDERS,
            # Отчеты
            Permission.VIEW_REPORTS,
            Permission.MANAGE_REPORTS,
            # Бонусная система
            Permission.VIEW_BONUSES,
            Permission.MANAGE_BONUSES,         # Может управлять бонусными программами
            # Управление клиентами
            Permission.MANAGE_CUSTOMERS,       # Может регистрировать посетителей
            # Профиль
            Permission.VIEW_PROFILE,
        ],
        # === БАРИСТА (barista) ===
        # Может регистрировать новых посетителей, начислять покупки,
        # проводить инвентаризацию, ставить напоминания
        UserRole.BARISTA: [
            # Инвентаризация
            Permission.VIEW_INVENTORY,
            Permission.MANAGE_INVENTORY,       # Может проводить инвентаризацию
            # Напоминания
            Permission.VIEW_REMINDERS,
            Permission.MANAGE_REMINDERS,       # Может ставить напоминания
            # Бонусная система
            Permission.VIEW_BONUSES,
            Permission.VIEW_REPORTS,
            # Управление клиентами
            Permission.MANAGE_CUSTOMERS,       # Может регистрировать и начислять покупки
            # Профиль
            Permission.VIEW_PROFILE,
        ],
        # === ПОСЕТИТЕЛЬ (visitor) ===
        # Может видеть только свой профиль и данные по бонусам
        UserRole.VISITOR: [
            # Бонусная система
            Permission.VIEW_BONUSES,           # Может видеть только свои бонусы
            # Профиль
            Permission.VIEW_PROFILE,           # Может видеть только свой профиль
        ],
        UserRole.GUEST: [
            # Профиль
            Permission.VIEW_PROFILE,           # Может видеть только свой профиль
        ],
    }
    
    # Отображение русских названий ролей
    ROLE_NAMES = {
        UserRole.ADMIN: "Администратор",
        UserRole.MANAGER: "Менеджер",
        UserRole.BARISTA: "Бариста",
        UserRole.VISITOR: "Клиент",
        UserRole.GUEST: "Гость",
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_user_role(self, user_id: int) -> UserRole:
        """Получает роль пользователя"""
        conn = None
        try:
            with sqlite_connection() as conn: 
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT role FROM user_roles WHERE user_id = ?", 
                    (user_id,)
                )

                result = cursor.fetchone()
                
                if result:
                    try:
                        role = UserRole(result['role'])
                        return role
                    except ValueError:
                        self.logger.warning(f"Неизвестная роль в БД: {result['role']}")
                        return UserRole.GUEST  # Дефолтная роль

                    # Если пользователя нет в БД, добавляем с дефолтной ролью
                self.logger.info(f"Новый пользователь {user_id}, устанавливаем роль Гость")
                #  conn.rollback()  # Откатываем текущую транзакцию
                return await self.set_user_role(user_id, UserRole.GUEST)
                
        except Exception as e:
            self.logger.error(f"Ошибка получения роли пользователя {user_id}: {e}")
            return UserRole.GUEST
       
    async def set_user_role(self, user_id: int, role: UserRole) -> UserRole:
        """Устанавливает роль пользователю"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_roles (user_id, role, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, role.value))
                
                conn.commit()
                self.logger.info(f"Установлена роль {role.value} для пользователя {user_id}")
                return role
                
        except Exception as e:
            self.logger.error(f"Ошибка установки роли для пользователя {user_id}: {e}")
            return UserRole.GUEST
    
    async def has_permission(self, user_id: int, permission: Permission) -> bool:
        """Проверяет, есть ли у пользователя разрешение"""
        try:
            # Получаем роль пользователя
            role = await self.get_user_role(user_id)
           
            # Получаем список разрешений для этой роли
            role_permissions = self.ROLE_PERMISSIONS.get(role, [])
            # Проверяем наличие нужного разрешения
            
            has_perm = permission in role_permissions
            
            # Логируем для отладки
            if not has_perm:
                self.logger.debug(f"У пользователя {user_id} (роль: {role.value}) нет разрешения {permission.value}")
            
            return has_perm
        
        except Exception as e:
            self.logger.error(f"Ошибка проверки разрешения: {e}")
            return False
       
    async def change_user_role(self, admin_id: int, target_user_id: int, new_role: UserRole) -> bool:
        """Изменяет роль пользователя (только для админов)"""
        try:
            # Проверяем, что администратор имеет право управлять ролями
            if not await self.has_permission(admin_id, Permission.MANAGE_ROLES):
                return False
            
            await self.set_user_role(target_user_id, new_role)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка изменения роли: {e}")
            return False
    
    def get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Получает список разрешений для роли"""
        return self.ROLE_PERMISSIONS.get(role, [])
    
    def get_role_name(self, role: UserRole) -> str:
        """Получает русское название роли"""
        role_names = {
            UserRole.ADMIN: "👑 Администратор",
            UserRole.MANAGER: "👔 Менеджер",
            UserRole.BARISTA: "☕ Бариста",
            UserRole.VISITOR: "👤 Клиент",
            UserRole.GUEST: "👤 Гость"
        }
        return role_names.get(role, "👤 Гость")
      
    def get_all_roles_info(self) -> List[Dict]:
        """Получает информацию о всех ролях"""
        roles_info = []
        
        for role in UserRole:
            permissions = self.get_role_permissions(role)
            roles_info.append({
                'role': role.value,
                'role_name': self.get_role_name(role),
                'permissions': [p.value for p in permissions],
                'permission_count': len(permissions),
                'can_manage_customers': self.can_manage_customers(role),
                'can_manage_inventory': self.can_manage_inventory(role),
                'can_view_reports': self.can_view_reports(role),
                'can_manage_reminds': self.can_manage_reminds(role),
                'can_manage_users': self.can_manage_users(role),
                'can_manage_system': self.can_manage_system(role)
            })
    
        return roles_info
    
    def escape_markdown_v2(self, text: str) -> str:
        """Экранирует спецсимволы для MarkdownV2"""
        if not text:
            return ""
        
        # Список символов, которые нужно экранировать в MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        
        result = ""
        for char in text:
            if char in escape_chars:
                result += '\\' + char
            else:
                result += char
        
        return result
    
    def can_manage_customers(self, role: UserRole) -> bool:
        """Проверяет, может ли роль управлять клиентами"""
        return role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.BARISTA]
    
    def can_manage_bonus_programs(self, role: UserRole) -> bool:
        """Проверяет, может ли роль управлять бонусными программами"""
        return role in [UserRole.ADMIN]
    
    def can_manage_users(self, role: UserRole) -> bool:
        """Проверяет, может ли роль управлять пользователями"""
        return role in [UserRole.ADMIN]
    
    def can_manage_system(self, role: UserRole) -> bool:
        """Проверяет, может ли роль управлять system"""
        return role in [UserRole.ADMIN]
    
    def can_view_reports(self, role: UserRole) -> bool:
        """Проверяет, может ли роль просматривать отчеты"""
        return role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.BARISTA]
    
    def can_manage_inventory(self, role: UserRole) -> bool:
        """Проверяет, может ли роль управлять инвентарем"""
        return role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.BARISTA]
    
    def can_confirm_inventory(self, role: UserRole) -> bool:
        """Проверяет, может ли роль подтверждать инвентарь"""
        return role in [UserRole.ADMIN, UserRole.MANAGER]

    def can_manage_reminds(self, role: UserRole) -> bool:
        """Проверяет, может ли управлять напоминаниями"""
        return role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.BARISTA]
# ====================================================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР МЕНЕДЖЕРА РОЛЕЙ
# Импортируется в другие модули для проверки прав
# ====================================================================
role_manager = RoleManager()