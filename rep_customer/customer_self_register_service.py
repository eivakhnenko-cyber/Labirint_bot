import logging
import re
import random
import string
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from .customer_repository import CustomerRepository
from handlers.admin_roles_class import UserRole
from models.customer_models import CustomerRegistrationDTO, CustomerDTO

logger = logging.getLogger(__name__)

class CustomerSelfRegisterService:
    """Сервис для бизнес-логики самостоятельной регистрации клиентов"""
    
    def __init__(self):
        self.repository = CustomerRepository()
    
    def validate_and_format_phone(self, phone_input: str) -> Optional[str]:
        """Валидирует и форматирует номер телефона"""
        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', phone_input)
        
        # Проверяем длину и формат
        if len(digits) == 11 and digits.startswith(('8', '7')):
            return f"+7{digits[1:]}"
        elif len(digits) == 10:
            return f"+7{digits}"
        elif len(digits) == 12 and digits.startswith('7'):
            return f"+{digits}"
        
        return None
    
    def validate_birthday(self, birthday_str: str) -> Optional[str]:
        """Валидирует дату рождения"""
        try:
            birthday = datetime.strptime(birthday_str, "%d.%m.%Y")
            
            # Проверяем, что дата не в будущем
            if birthday > datetime.now():
                return None
            
            # Проверяем, что человек не старше 150 лет
            if birthday.year < datetime.now().year - 150:
                return None
            
            return birthday.strftime("%Y-%m-%d")
            
        except ValueError:
            return None
    
    def generate_card_number(self) -> str:
        """Генерирует уникальный номер карты"""
        prefix = "LBC"
        
        while True:
            # Генерируем случайный номер
            numbers = ''.join(random.choices(string.digits, k=12))
            card_number = f"{prefix}-{numbers[:4]}-{numbers[4:8]}-{numbers[8:12]}"
            
            # Проверяем уникальность
            if self.repository.is_card_number_unique(card_number):
                return card_number
    
    def check_phone_availability(self, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет доступность номера телефона для регистрации
        
        Returns:
            Tuple[is_available: bool, error_message: Optional[str]]
        """
        # Валидируем номер
        formatted_phone = self.validate_and_format_phone(phone)
        if not formatted_phone:
            return False, "Неверный формат номера телефона"
        
        # Проверяем, не зарегистрирован ли уже
        if self.repository.is_phone_registered(formatted_phone):
            return False, f"Номер телефона {formatted_phone} уже зарегистрирован"
        
        return True, formatted_phone
    
    def prepare_customer_data(self, telegram_id: int, first_name: str, 
                             username: str, phone: str, 
                             birthday: Optional[str] = None) -> Dict[str, Any]:
        """Подготавливает данные клиента для регистрации"""
        return {
            'telegram_id': telegram_id,
            'first_name': first_name,
            'username': username or first_name,
            'phone': phone,
            'birthday': birthday,
            'card_number': self.generate_card_number()
        }
    
    def register_customer(self, customer_data: Dict[str, Any]) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Регистрирует нового клиента
        
        Returns:
            Tuple[success: bool, customer_id: Optional[int], error_message: Optional[str]]
        """
        try:
            # 1. Получаем или обновляем пользователя
            user_id = self.repository.update_user_for_customer(
                telegram_id=customer_data['telegram_id'],
                username=customer_data['username'],
                first_name=customer_data['first_name'],
                phone=customer_data['phone']
            )
            
            if not user_id:
                return False, None, "Ошибка обновления данных пользователя"
            
            # 2. Обновляем роль пользователя
            if not self.repository.update_user_role(user_id, UserRole.VISITOR.value):
                logger.warning(f"Не удалось обновить роль для user_id {user_id}")
            
            # 3. Создаем запись клиента
            customer_id = self.repository.create_customer(
                user_id=user_id,
                username=customer_data['username'],
                phone=customer_data['phone'],
                birthday=customer_data.get('birthday'),
                card_number=customer_data['card_number']
            )
            
            if not customer_id:
                return False, None, "Ошибка создания клиента"
            
            return True, customer_id, None
            
        except Exception as e:
            logger.error(f"Ошибка регистрации клиента: {e}", exc_info=True)
            return False, None, f"Внутренняя ошибка: {str(e)}"
    
    def format_registration_message(self, customer_data: Dict[str, Any], 
                                   customer_id: int) -> str:
        """Форматирует сообщение об успешной регистрации"""
        message = (
            f"🎉 *Поздравляем! Вы успешно зарегистрированы!*\n\n"
            f"👤 *Имя:* {customer_data['first_name']}\n"
            f"📱 *Телефон:* {customer_data['phone']}\n"
        )
        
        if customer_data.get('birthday'):
            try:
                birth_date = datetime.strptime(customer_data['birthday'], "%Y-%m-%d")
                message += f"🎂 *Дата рождения:* {birth_date.strftime('%d.%m.%Y')}\n"
            except:
                pass
        
        message += (
            f"💳 *Номер карты:* {customer_data['card_number']}\n"
            f"🆔 *Ваш ID:* {customer_id}\n\n"
            f"✅ Теперь вам доступна бонусная программа!\n"
            f"Сохраните номер карты для использования в кофейне."
        )
        
        return message
    
    def prepare_customer_dto(self, telegram_id: int, first_name: str, 
                            username: str, phone: str, 
                            birthday: Optional[str] = None) -> CustomerRegistrationDTO:
        """Создает DTO для регистрации клиента"""
        return CustomerRegistrationDTO(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username or first_name,
            phone=phone,
            birthday=birthday,
            card_number=self.generate_card_number(),
            registration_date=datetime.now()
        )
    
    def register_customer_dto(self, customer_dto: CustomerRegistrationDTO) -> Tuple[bool, Optional[CustomerDTO], Optional[str]]:
        """
        Регистрирует клиента используя DTO
        
        Returns:
            Tuple[success: bool, customer_dto: Optional[CustomerDTO], error_message: Optional[str]]
        """
        try:
            # 1. Получаем или обновляем пользователя
            user_id = self.repository.update_user_for_customer(
                telegram_id=customer_dto.telegram_id,
                username=customer_dto.username,
                first_name=customer_dto.first_name,
                phone=customer_dto.phone
            )
            
            if not user_id:
                return False, None, "Ошибка обновления данных пользователя"
            
            # 2. Обновляем роль пользователя
            if not self.repository.update_user_role(user_id, UserRole.VISITOR.value):
                logger.warning(f"Не удалось обновить роль для user_id {user_id}")
            
            # 3. Обновляем DTO с user_id
            customer_dto.user_id = user_id
            
            # 4. Создаем клиента
            customer = self.repository.create_customer_dto(customer_dto)
            
            if not customer:
                return False, None, "Ошибка создания клиента"
            
            return True, customer, None
            
        except Exception as e:
            logger.error(f"Ошибка регистрации клиента: {e}", exc_info=True)
            return False, None, f"Внутренняя ошибка: {str(e)}"