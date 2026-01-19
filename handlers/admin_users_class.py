# handlers/users_class.py
import logging
from typing import Dict, List
from database import sqlite_connection
from .admin_roles_class import role_manager, Permission, UserRole



logger = logging.getLogger(__name__)


class UserManager:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def add_user(self, user_id: int, role: UserRole = UserRole.BARISTA) -> bool:
        """Добавляет нового пользователя в систему"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
            
                # Проверяем, существует ли пользователь
                cursor.execute(
                    "SELECT role FROM user_roles WHERE user_id = ?",
                    (user_id,)
                )
                
                if cursor.fetchone():
                    self.logger.warning(f"Пользователь {user_id} уже существует в системе")
                    return False
                
                # Добавляем пользователя
                cursor.execute('''
                    INSERT INTO user_roles (user_id, role, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, role.value))
                
                conn.commit()
                self.logger.info(f"Пользователь {user_id} добавлен с ролью {role.value}")
                return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления пользователя {user_id}: {e}")
            return False
        
    async def delete_user(self, admin_id: int, target_user_id: int) -> bool:
        """Удаляет пользователя из системы"""
        try:
        # Проверяем права администратора
            if not await role_manager.has_permission(admin_id, Permission.MANAGE_USERS):
                return False
        
        # Нельзя удалить себя
            if admin_id == target_user_id:
                return False
        
            with sqlite_connection() as conn:
                cursor = conn.cursor()
            
                # Получаем роль пользователя
                cursor.execute(
                    "SELECT role FROM user_roles WHERE user_id = ?",
                    (target_user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                # Нельзя удалять администраторов, кроме самого администратора
                if result['role'] == UserRole.ADMIN.value:
                    # Проверяем, сколько осталось админов
                    cursor.execute(
                        "SELECT COUNT(*) as admin_count FROM user_roles WHERE role = ?",
                        (UserRole.ADMIN.value,)
                    )
                    admin_count = cursor.fetchone(['admin_count'])
                    
                    if admin_count <= 1:
                        return False  # Нельзя удалить последнего администратора
                
                # Удаляем пользователя
                cursor.execute(
                    "DELETE FROM user_roles WHERE user_id = ?",
                    (target_user_id,)
                )
                cursor.execute(
                    "DELETE FROM users WHERE user_id = ?", 
                    (target_user_id,))
                
                conn.commit()
                self.logger.info(f"Пользователь {target_user_id} удален из системы")
                return True
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления пользователя {target_user_id}: {e}")
            return False

    async def update_user_info(self, user_id: int, **kwargs) -> bool:
        """Обновляет информацию о пользователе в таблице users"""
        try:
            allowed_fields = ['username', 'first_name', 'last_name', 'phone_numb']
            
            # Фильтруем только разрешенные поля
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                return False
            
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем, существует ли запись в users
                cursor.execute(
                    "SELECT 1 FROM users WHERE user_id = ?",
                    (user_id,)
                )
                
                if cursor.fetchone():
                    # Обновляем существующую запись
                    set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
                    values = list(update_fields.values())
                    values.append(user_id)
                    
                    query = f"UPDATE users SET {set_clause} WHERE user_id = ?"
                    cursor.execute(query, values)
                else:
                    # Создаем новую запись
                    fields = list(update_fields.keys()) + ['user_id']
                    placeholders = ', '.join(['?'] * len(fields))
                    
                    query = f"INSERT INTO users ({', '.join(fields)}) VALUES ({placeholders})"
                    values = [update_fields.get(field) for field in update_fields.keys()] + [user_id]
                    
                    cursor.execute(query, values)
                
                conn.commit()
                self.logger.info(f"Информация пользователя {user_id} обновлена")
                return True
       
        except AttributeError:
        # Если метод не существует, используем прямое обращение к БД
            try:
                with sqlite_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Проверяем, существует ли запись в users
                    cursor.execute(
                        "SELECT 1 FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    
                    if cursor.fetchone():
                        # Обновляем существующую запись
                        set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
                        values = list(update_fields.values())
                        values.append(user_id)
                        
                        query = f"UPDATE users SET {set_clause} WHERE user_id = ?"
                        cursor.execute(query, values)
                    else:
                        # Создаем новую запись
                        fields = list(update_fields.keys()) + ['user_id']
                        placeholders = ', '.join(['?'] * len(fields))
                        
                        query = f"INSERT INTO users ({', '.join(fields)}) VALUES ({placeholders})"
                        values = [update_fields.get(field) for field in update_fields.keys()] + [user_id]
                        
                        cursor.execute(query, values)
                    
                    conn.commit()
                    self.logger.info(f"Информация пользователя {user_id} обновлена")
                    return True
                            
            except Exception as db_error:
                self.logger.error(f"Ошибка БД при редактировании пользователя: {db_error}")
                return False

    async def get_users_without_visitors(self) -> List[Dict]:
        """Получает список пользователей без посетителей"""
        try:

            with sqlite_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT ur.user_id, ur.role, ur.created_at, ur.updated_at,
                        u.username, u.first_name, u.last_name
                    FROM user_roles ur
                    LEFT JOIN users u ON ur.user_id = u.user_id
                    WHERE ur.role != ?
                    ORDER BY ur.role, ur.user_id
                ''', (UserRole.VISITOR.value,))
                
                users = []
                for row in cursor.fetchall():
                     # Получаем роль как объект UserRole
                    try:
                        role_obj = UserRole(row['role'])
                        role_name = role_manager.get_role_name(role_obj)
                    except (ValueError, KeyError):
                        role_name = "Неизвестно"
                    users.append({
                        'user_id': row['user_id'],
                        'role': row['role'],
                        'role_name': role_name,
                        'username': row['username'] or 'Не указан',
                        'first_name': row['first_name'] or 'Не указано',
                        'last_name': row['last_name'] or 'Не указано',
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return users
            self.logger.info(f"список получен: {users}") 

        except Exception as e:
            self.logger.error(f"Ошибка получения списка пользователей без посетителей: {e}")
            return []
        
    async def get_all_users(self) -> List[Dict]:
        """Получает список всех пользователей с их ролями"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, role, created_at, updated_at 
                    FROM user_roles 
                    ORDER BY role, user_id
                ''')
                
                users = []
                for row in cursor.fetchall():
                    try:
                        role_obj = UserRole(row['role'])
                        role_name = role_manager.get_role_name(role_obj)
                    except (ValueError, KeyError):
                        role_name = "Неизвестно"
                        users.append({
                            'user_id': row['user_id'],
                            'role': row['role'],
                            'role_name': role_name,
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at']
                        })
                
                return users
            self.logger.info(f"список получен: {users}") 

        except Exception as e:
            self.logger.error(f"Ошибка получения списка пользователей: {e}")
            return []
    
    async def check_user_in_users_table(self, user_id: int) -> bool:
        """Проверяет, существует ли пользователь в таблице users"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM users WHERE user_id = ?",
                    (user_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Ошибка проверки пользователя в таблице users: {e}")
        return False

    async def add_user_to_users_table(self, user_id: int, telegram_user=None) -> bool:
        """Добавляет пользователя в таблицу users"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем, не существует ли уже пользователь
                cursor.execute(
                    "SELECT 1 FROM users WHERE user_id = ?",
                    (user_id,)
                )
                
                if cursor.fetchone():
                    return True  # Уже существует
                
                # Добавляем нового пользователя
                cursor.execute('''
                    INSERT INTO users (user_id, telegram_id, username, first_name, last_name, phone_numb, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    user_id,
                    telegram_user.username if telegram_user else None,
                    telegram_user.first_name if telegram_user else None,
                    telegram_user.last_name if telegram_user else None,
                    telegram_user.phone_number if telegram_user else None
                ))
                
                conn.commit()
                self.logger.info(f"Пользователь {user_id} добавлен в таблицу users")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка добавления пользователя в таблицу users: {e}")
            return False
        
users_manager = UserManager()