from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CustomerRegistrationDTO:
    """DTO для регистрации клиента"""
    telegram_id: int
    first_name: str
    username: str
    phone: str
    birthday: Optional[str] = None
    card_number: Optional[str] = None
    registration_date: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Конвертирует DTO в словарь"""
        return {
            'telegram_id': self.telegram_id,
            'first_name': self.first_name,
            'username': self.username,
            'phone': self.phone,
            'birthday': self.birthday,
            'card_number': self.card_number,
            'registration_date': self.registration_date.isoformat() 
                if self.registration_date else None
        }

@dataclass
class CustomerDTO:
    """DTO для клиента"""
    customer_id: int
    user_id: int
    username: str
    phone_number: str
    birthday: Optional[str]
    card_number: str
    registration_date: datetime
    is_active: bool
    total_purchases: float
    total_bonuses: float
    available_bonuses: float
    bonus_program_id: Optional[int] = None
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'CustomerDTO':
        """Создает DTO из строки БД"""
        return cls(
            customer_id=row['customer_id'],
            user_id=row['user_id'],
            username=row['username'],
            phone_number=row['phone_number'],
            birthday=row['birthday'],
            card_number=row['card_number'],
            registration_date=datetime.fromisoformat(row['registration_date']),
            is_active=bool(row['is_active']),
            total_purchases=row['total_purchases'],
            total_bonuses=row['total_bonuses'],
            available_bonuses=row['available_bonuses'],
            bonus_program_id=row.get('bonus_program_id')
        )