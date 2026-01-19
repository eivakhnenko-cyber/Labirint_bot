import logging
from typing import List, Dict, Optional
from database import sqlite_connection

logger = logging.getLogger(__name__)


class CatalogRepository:
    """Репозиторий для работы со справочником товаров"""
    
    @staticmethod
    def get_active_categories() -> List[str]:
        """Получить список активных категорий"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT category 
                    FROM product_catalog 
                    WHERE is_active = 1 
                    ORDER BY category
                ''')
                return [row['category'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            return []
    
    @staticmethod
    def get_category_products(category: str) -> List[Dict]:
        """Получить товары категории"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT product_id, name, unit, default_quantity, description
                    FROM product_catalog 
                    WHERE category = ? AND is_active = 1
                    ORDER BY name
                ''', (category,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения товаров категории: {e}")
            return []
    
    @staticmethod
    def check_category_exists(category: str) -> bool:
        """Проверить существование категории с активными товарами"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM product_catalog 
                    WHERE category = ? AND is_active = 1
                ''', (category,))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            logger.error(f"Ошибка проверки категории: {e}")
            return False
    
    @staticmethod
    def check_product_name_exists(name: str) -> bool:
        """Проверить существование товара с таким названием"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT product_id FROM product_catalog WHERE name = ?",
                    (name,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки названия: {e}")
            return False
    
    @staticmethod
    def add_product(
        category: str,
        name: str,
        unit: str,
        default_quantity: float,
        description: Optional[str] = None
    ) -> Optional[int]:
        """Добавить товар в справочник"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO product_catalog (
                        category, name, unit, default_quantity, description
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (category, name, unit, default_quantity, description))
                product_id = cursor.lastrowid
                conn.commit()
                return product_id
        except Exception as e:
            logger.error(f"Ошибка добавления товара: {e}")
            return None
    
    @staticmethod
    def soft_delete_product(product_id: int) -> bool:
        """Мягкое удаление товара (установка is_active = 0)"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE product_catalog 
                    SET is_active = 0,
                        deleted_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                ''', (product_id,))
                success = cursor.rowcount > 0
                conn.commit()
                return success
        except Exception as e:
            logger.error(f"Ошибка удаления товара: {e}")
            return False
    
    @staticmethod
    def soft_delete_category_products(category: str) -> int:
        """Мягкое удаление всех товаров категории"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE product_catalog 
                    SET is_active = 0,
                        deleted_at = CURRENT_TIMESTAMP
                    WHERE category = ? AND is_active = 1
                ''', (category,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            logger.error(f"Ошибка удаления товаров категории: {e}")
            return 0
    
    @staticmethod
    def get_all_categories_with_counts() -> List[Dict]:
        """Получить все категории с количеством товаров"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT category, COUNT(*) as count 
                    FROM product_catalog 
                    WHERE is_active = 1 
                    GROUP BY category 
                    ORDER BY category
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения категорий с количеством: {e}")
            return []
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Dict]:
        """Получить товар по ID"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT product_id, name, unit, default_quantity, description, category
                    FROM product_catalog 
                    WHERE product_id = ? AND is_active = 1
                ''', (product_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения товара по ID: {e}")
            return None
    
    @staticmethod
    def update_product(
        product_id: int,
        category: Optional[str] = None,
        name: Optional[str] = None,
        unit: Optional[str] = None,
        default_quantity: Optional[float] = None,
        description: Optional[str] = None
    ) -> bool:
        """Обновить информацию о товаре"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Формируем динамический запрос
                updates = []
                params = []
                
                if category is not None:
                    updates.append("category = ?")
                    params.append(category)
                
                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                
                if unit is not None:
                    updates.append("unit = ?")
                    params.append(unit)
                
                if default_quantity is not None:
                    updates.append("default_quantity = ?")
                    params.append(default_quantity)
                
                if description is not None:
                    updates.append("description = ?")
                    params.append(description)
                
                if not updates:
                    return False
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                
                query = f'''
                    UPDATE product_catalog 
                    SET {', '.join(updates)}
                    WHERE product_id = ?
                '''
                params.append(product_id)
                
                cursor.execute(query, tuple(params))
                success = cursor.rowcount > 0
                conn.commit()
                return success
                
        except Exception as e:
            logger.error(f"Ошибка обновления товара: {e}")
            return False
    
    @staticmethod
    def update_category(old_category: str, new_category: str) -> int:
        """Обновить название категории во всех товарах"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE product_catalog 
                    SET category = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE category = ? AND is_active = 1
                ''', (new_category, old_category))
                updated_count = cursor.rowcount
                conn.commit()
                return updated_count
        except Exception as e:
            logger.error(f"Ошибка обновления категории: {e}")
            return 0
    
    @staticmethod
    def search_products(
        search_term: str,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Поиск товаров по названию или описанию"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute('''
                        SELECT product_id, name, unit, default_quantity, description, category
                        FROM product_catalog 
                        WHERE category = ? 
                          AND is_active = 1
                          AND (name LIKE ? OR description LIKE ?)
                        ORDER BY name
                    ''', (category, f'%{search_term}%', f'%{search_term}%'))
                else:
                    cursor.execute('''
                        SELECT product_id, name, unit, default_quantity, description, category
                        FROM product_catalog 
                        WHERE is_active = 1
                          AND (name LIKE ? OR description LIKE ?)
                        ORDER BY category, name
                    ''', (f'%{search_term}%', f'%{search_term}%'))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка поиска товаров: {e}")
            return []