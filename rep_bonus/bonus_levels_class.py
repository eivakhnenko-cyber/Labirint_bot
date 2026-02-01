
import logging
from database import sqlite_connection 

logger = logging.getLogger(__name__)

class BunusLevelsManager:
    """Упраавление уровнями программ"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_bonus_level(self, program_id: int, level_name: str, min_total_purchases: float, 
                      bonus_percent: float, description: str = None):
        """Создание нового уровня в бонусной программе"""

        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO bonus_levels 
                    (program_id, level_name, min_total_purchases, bonus_percent, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (program_id, level_name, min_total_purchases, bonus_percent, description))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Ошибка создания уровня: {e}")
            return None

    def get_bonus_levels(self, program_id: int = None):
        """Получение списка уровней"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                if program_id:
                    cursor.execute('''
                        SELECT bl.*, bp.program_name 
                        FROM bonus_levels bl
                        JOIN bonus_programs bp ON bl.program_id = bp.program_id
                        WHERE bl.program_id = ?
                        ORDER BY bl.min_total_purchases ASC
                    ''', (program_id,))
                else:
                    cursor.execute('''
                        SELECT bl.*, bp.program_name 
                        FROM bonus_levels bl
                        JOIN bonus_programs bp ON bl.program_id = bp.program_id
                        ORDER BY bp.program_name, bl.min_total_purchases ASC
                    ''')
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения уровней: {e}")
            return []

    def get_bonus_level(self, level_id: int):
        """Получение уровня по ID"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT bl.*, bp.program_name 
                    FROM bonus_levels bl
                    JOIN bonus_programs bp ON bl.program_id = bp.program_id
                    WHERE bl.level_id = ?
                ''', (level_id,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Ошибка получения уровня: {e}")
            return None

    def update_bonus_level(self,level_id: int, **kwargs):
        """Обновление уровня"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Формируем динамический запрос
                fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['level_name', 'min_total_purchases', 'bonus_percent', 'description']:
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return False
                    
                values.append(level_id)
                query = f"UPDATE bonus_levels SET {', '.join(fields)} WHERE level_id = ?"
                
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Ошибка обновления уровня: {e}")
            return False

    def delete_bonus_level(self, level_id: int):
        """Удаление уровня"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM bonus_levels WHERE level_id = ?', (level_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Ошибка удаления уровня: {e}")
            return False

    def get_active_bonus_programs(self):
        """Получение активных бонусных программ для выбора"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT program_id, program_name 
                    FROM bonus_programs 
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения программ: {e}")
            return []

    async def get_current_level_info(self, total_purchases: float, program_id: int) -> str:
        """Получает информацию о текущем уровне клиента"""
        try:
            with sqlite_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем уровни программы
                cursor.execute('''
                    SELECT level_name, bonus_percent, min_total_purchases,
                        (SELECT MIN(min_total_purchases) FROM bonus_levels 
                            WHERE program_id = ? AND min_total_purchases > ?) as next_level_min
                    FROM bonus_levels 
                    WHERE program_id = ? AND min_total_purchases <= ?
                    ORDER BY min_total_purchases DESC
                    LIMIT 1
                ''', (program_id, total_purchases, program_id, total_purchases))
                
                current_level = cursor.fetchone()
                
                if current_level:
                    info = f"{current_level['level_name']} ({current_level['bonus_percent']}%)"
                    
                    # Показываем прогресс до следующего уровня
                    if current_level['next_level_min']:
                        remaining = current_level['next_level_min'] - total_purchases
                        info += f"\nДо следующего уровня: {remaining:.2f} руб."
                        
                    return info
                    
                return "Базовый уровень"
                
        except Exception as e:
            self.logger.error(f"Ошибка получения информации об уровне: {e}")
            return ""
        
bonus_levels_manager = BunusLevelsManager()