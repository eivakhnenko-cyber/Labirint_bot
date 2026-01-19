# handlers/bonus_master.py
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
import decimal

from handlers.admin_roles_class import role_manager, Permission, UserRole
from rep_bonus.bonus_master_class import bonus_data_manager
from rep_customer.customer_purchase_class import customer_purchase
from keyboards.global_keyb import get_main_keyboard, get_cancel_keyboard
from keyboards.bonus_keyb import get_confirm_bonus_keyboard, get_bonus_system_keyboard, get_loyalty_program_keyboard
from rep_bonus.bonus_levels_class import bonus_levels_manager
from config.buttons import Buttons

logger = logging.getLogger(__name__)


async def bonus_system(update: Update, context: CallbackContext) -> None:
    """
    ГЛАВНОЕ МЕНЮ БОНУСНОЙ СИСТЕМЫ
    Привязывается к кнопке "Бонусная система" в главном меню.
    Показывает разные интерфейсы в зависимости от роли пользователя.
    """
    try:
        user_id = update.effective_user.id
        
        if not await role_manager.has_permission(user_id, Permission.VIEW_BONUSES):
            await update.message.reply_text(
                "❌ У вас нет доступа к бонусной системе.",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
        
        message = "🎁 Бонусная система\n\n"
        
        # Получаем роль пользователя
        role = await role_manager.get_user_role(user_id)
        
        # Для посетителей (зарегистрированных клиентов)
        if role == UserRole.VISITOR:
            # Получаем данные клиента через менеджер данных
            customer_data = bonus_data_manager.get_customer_bonus_data(user_id)
            
            if customer_data:
                # Рассчитываем текущий бонусный процент
                current_bonus = customer_purchase.calculate_current_bonus_percent(
                    customer_data['total_purchases'],
                    customer_data['bonus_program_id']
                )
                
                # Получаем информацию о текущем уровне
                level_info = ""
                try:
                    level_info = await bonus_levels_manager.get_current_level_info(
                        customer_data['total_purchases'],
                        customer_data['bonus_program_id']
                    )
                except:
                    level_info = ""
                
                message += (
                    f"👤 *Ваш профиль:* {customer_data['username']}\n"
                    f"💳 *Номер карты:* {customer_data['card_number']}\n"
                    f"💰 *Общая сумма покупок:* {customer_data['total_purchases']:.2f} руб.\n"
                    f"🎫 *Всего накоплено бонусов:* {customer_data['total_bonuses']:.2f} руб.\n"
                    f"💎 *Доступно бонусов:* {customer_data['available_bonuses']:.2f} руб.\n"
                    f"🛒 *Количество покупок:* {customer_data['purchase_count']}\n"
                    f"📊 *Текущий бонусный %:* {current_bonus}%\n"
                )
                
                if level_info:
                    message += f"🏆 *Текущий уровень:* {level_info}\n"
                
                if customer_data['program_name']:
                    message += f"\n📋 *Бонусная программа:* {customer_data['program_name']}\n"
                    message += f"💡 *Базовый процент:* {customer_data['base_percent'] or 0}%\n"
                
                # Дополнительная статистика
                spent_bonuses = customer_data['spent_bonuses']
                if spent_bonuses > 0:
                    message += f"🔄 *Использовано бонусов:* {spent_bonuses:.2f} руб.\n"
                    message += "\n*Как использовать бонусы:*\n"
                    message += "• Каждая покупка приносит бонусные баллы\n"
                    message += f"• Вы получаете {current_bonus}% от суммы каждой покупки\n"
                    message += "• Бонусами можно оплачивать до 30% от суммы заказа\n"
                    message += "• Бонусы не имеют срока действия\n"
            else:
                message += "📝 *Вы еще не зарегистрированы как клиент.*\n\n"
                message += "Чтобы участвовать в бонусной программе:\n"
                message += "1. Обратитесь к администратору\n"
                message += "2. Получите бонусную карту\n"
                message += "3. Начинайте копить бонусы!\n"
        
        # Для администратора
        elif role == UserRole.ADMIN:
            message += (
                "👑 *Режим администратора*\n\n"
                "Добро пожаловать в управление программой лояльности!\n\n"
                "*Доступные функции:*\n"
                "• 🎫 Управление программами\n"
                "• 🏆 Управление уровнями\n"
                "• 🏷️ Промокоды\n"
                "• 📊 Статистика\n"
                "• 👥 Управление клиентами\n"
            )
        
        # Для менеджера
        elif role == UserRole.MANAGER:
            message += (
                "👔 *Режим менеджера*\n\n"
                "Добро пожаловать в систему лояльности для клиентов\n\n"
                "*Доступные функции:*\n"
                "• 🎫 Проверка бонусов клиента\n"
                "• ➕ Начисление бонусов\n"
                "• ➖ Списание бонусов\n"
                "• 📊 Статистика\n"
                "• 🔍 Поиск клиентов\n"
            )
        
        await update.message.reply_text(
            message,
            reply_markup=await get_bonus_system_keyboard(user_id),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в bonus_system: {e}")
        await update.message.reply_text(
            "❌ Ошибка загрузки бонусной системы.",
            reply_markup=await get_main_keyboard(user_id)
        )

async def manage_bonus_programs(update: Update, context: CallbackContext) -> None:
    """Меню управления бонусными программами"""
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if not role_manager.can_manage_bonus_programs(role):
        await update.message.reply_text(
            "⛔ У вас нет прав для управления бонусными программами.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    await update.message.reply_text(
        "🎁 *Управление бонусными программами*\n\n"
        "Выберите действие:",
        reply_markup=await get_bonus_system_keyboard(user_id),
        parse_mode='Markdown'
    )

async def create_bonus_program(update: Update, context: CallbackContext) -> None:
    """
    НАЧАЛО СОЗДАНИЯ БОНУСНОЙ ПРОГРАММЫ
    Привязывается к кнопке "Создать программу".
    Начинает процесс создания новой бонусной программы.
    """
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if role != UserRole.ADMIN:
        await update.message.reply_text(
            "⛔ Только администратор может создавать бонусные программы.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Устанавливаем процесс создания программы
    context.user_data['creating_program'] = {
        'step': 'name',
        'data': {}
    }
    
    await update.message.reply_text(
        f"{Buttons.ADD_PROGRAM} \nВведите название программы:",
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown'
    )

async def process_program_creation(update: Update, context: CallbackContext) -> None:
    """
    ОБРАБОТКА СОЗДАНИЯ БОНУСНОЙ ПРОГРАММЫ (пошаговый процесс)
    Обрабатывает ввод данных на каждом шаге создания программы.
    Не привязывается к кнопке - вызывается из цепочки создания.
    """
    if 'creating_program' not in context.user_data:
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    process = context.user_data['creating_program']
    step = process['step']
    
    if text == Buttons.CANCEL:
        del context.user_data['creating_program']
        await update.message.reply_text(
            "❌ Создание программы отменено.",
            reply_markup=await get_loyalty_program_keyboard()
        )
        return
    
    if step == 'name':
        if not text:
            await update.message.reply_text("Введите название программы:")
            return
        
        # Проверяем, нет ли уже программы с таким названием
        if bonus_data_manager.check_program_name_exists(text):
            await update.message.reply_text(
                "❌ Программа с таким названием уже существует.\n"
                "Введите другое название:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        process['data']['name'] = text
        process['step'] = 'description'
        
        await update.message.reply_text(
            "📝 Введите описание программы (необязательно):\n"
            "Или нажмите 'Пропустить'",
            reply_markup=ReplyKeyboardMarkup(
                [["Пропустить", "❌ Отмена"]],
                resize_keyboard=True
            )
        )
    
    elif step == 'description':
        if text == "Пропустить":
            process['data']['description'] = None
        else:
            process['data']['description'] = text
        
        process['step'] = 'base_percent'
        
        await update.message.reply_text(
            "📊 Введите базовый процент начисления бонусов:\n"
            "Например: 5.0 для 5%",
            reply_markup=get_cancel_keyboard()
        )
    
    elif step == 'base_percent':
        try:
            percent = decimal.Decimal(text)
            if percent <= 0 or percent > 100:
                await update.message.reply_text(
                    "Процент должен быть от 0 до 100. Введите снова:",
                    reply_markup=get_cancel_keyboard()
                )
                return
            process['data']['base_percent'] = str(percent)
            process['step'] = 'min_amount'
            
            await update.message.reply_text(
                "💰 Введите минимальную сумму покупки для начисления бонусов:\n"
                "Например: 100.0 (0 если нет ограничения)",
                reply_markup=get_cancel_keyboard()
            )
        except:
            await update.message.reply_text(
                "Введите корректное число:",
                reply_markup=get_cancel_keyboard()
            )
    
    elif step == 'min_amount':
        try:
            amount = decimal.Decimal(text)
            if amount < 0:
                await update.message.reply_text(
                    "Сумма не может быть отрицательной. Введите снова:",
                    reply_markup=get_cancel_keyboard()
                )
                return
            process['data']['min_amount'] = str(amount)
            process['step'] = 'confirm'
            
            # Формируем текст подтверждения
            confirm_text = (
                "✅ *Данные бонусной программы:*\n\n"
                f"🏷️ *Название:* {process['data']['name']}\n"
                f"📝 *Описание:* {process['data']['description'] or 'Не указано'}\n"
                f"📊 *Базовый процент:* {process['data']['base_percent']}%\n"
                f"💰 *Мин. сумма:* {process['data']['min_amount']} руб.\n\n"
                "Создать программу?"
            )
            
            await update.message.reply_text(
                confirm_text,
                reply_markup=get_confirm_bonus_keyboard(),
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text(
                "Введите корректное число:",
                reply_markup=get_cancel_keyboard()
            )
    
    elif step == 'confirm':
        if text == "✅ Да":
            await save_bonus_program(update, context, process['data'], user_id)
        else:
            del context.user_data['creating_program']
            await update.message.reply_text(
                "❌ Создание программы отменено.",
                reply_markup=await get_loyalty_program_keyboard()
            )

async def save_bonus_program(update: Update, context: CallbackContext, 
                            program_data: dict, user_id: int) -> None:
    """
    СОХРАНЕНИЕ БОНУСНОЙ ПРОГРАММЫ В БД (вспомогательная функция)
    Сохраняет данные программы в базу данных через менеджер.
    Не вызывается напрямую пользователем.
    """
    program_id = bonus_data_manager.save_bonus_program(program_data, user_id)
    
    if program_id:
        del context.user_data['creating_program']
        
        await update.message.reply_text(
            f"✅ *Бонусная программа создана!*\n\n"
            f"🏷️ *Название:* {program_data['name']}\n"
            f"🆔 *ID программы:* {program_id}\n"
            f"📊 *Базовый процент:* {program_data['base_percent']}%\n"
            f"💰 *Мин. сумма:* {program_data['min_amount']} руб.\n\n"
            f"Теперь вы можете настроить уровни программы.",
            reply_markup=await get_loyalty_program_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка при создании программы. Попробуйте позже.",
            reply_markup=await get_loyalty_program_keyboard()
        )

async def list_bonus_programs(update: Update, context: CallbackContext) -> None:
    """
    СПИСОК БОНУСНЫХ ПРОГРАММ
    Привязывается к кнопке "Список программ".
    Показывает все существующие бонусные программы.
    """
    user_id = update.effective_user.id
    
    programs = bonus_data_manager.get_all_bonus_programs()
    
    if not programs:
        await update.message.reply_text(
            "📭 Бонусные программы не найдены.",
            reply_markup=await get_loyalty_program_keyboard()
        )
        return
    
    response = "🎁 *Список бонусных программ:*\n\n"
    
    for program in programs:
        status = "✅ Активна" if program['is_active'] else "❌ Неактивна"
        response += (
            f"🏷️ *{program['program_name']}*\n"
            f"🆔 ID: {program['program_id']}\n"
            f"📝 {program['description'] or 'Без описания'}\n"
            f"📊 Базовый %: {program['base_percent']}%\n"
            f"📊 Статус: {status}\n\n"
        )
    
    await update.message.reply_text(
        response,
        reply_markup=await get_loyalty_program_keyboard(),
        parse_mode='Markdown'
    )

async def assign_bonus_program(update: Update, context: CallbackContext) -> None:
    """
    НАЗНАЧЕНИЕ ПРОГРАММЫ ВСЕМ КЛИЕНТАМ
    Привязывается к кнопке "Назначить программу".
    Позволяет выбрать программу для назначения всем клиентам.
    """
    user_id = update.effective_user.id
    role = await role_manager.get_user_role(user_id)
    
    if role != UserRole.ADMIN:
        await update.message.reply_text(
            "⛔ Только администратор может назначать бонусные программы.",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Получаем список программ через менеджер данных
    programs = bonus_data_manager.get_active_bonus_programs()
    
    if not programs:
        await update.message.reply_text(
            "❌ Нет активных бонусных программ.",
            reply_markup=await get_loyalty_program_keyboard()
        )
        return
    
    # Формируем клавиатуру с программами
    buttons = []
    for program in programs:
        buttons.append([f"🎯 ID:{program['program_id']} - {program['program_name']}"])
    buttons.append([Buttons.CANCEL])
    
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        "🎁 *Назначение бонусной программы*\n\n"
        "Выберите программу для назначения всем клиентам:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    context.user_data['assigning_program'] = True