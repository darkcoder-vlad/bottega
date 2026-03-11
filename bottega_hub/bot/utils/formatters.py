from datetime import datetime
from typing import Optional


def format_progress(visits: int, required: int = 9, days_remaining: int = 60) -> str:
    """Format progress message"""
    remaining = required - visits
    status = f"Ваш прогресс: {visits} из {required} визитов\n"
    status += f"До награды осталось: {remaining} визитов\n"
    status += f"Времени осталось: {days_remaining} дней"
    return status


def format_visit_date(date: datetime) -> str:
    """Format visit date"""
    return date.strftime("%d.%m.%Y %H:%M")


def format_reward_code(code: str) -> str:
    """Format reward code display"""
    return f"🎁 Ваш код награды: {code}"


def format_user_info(user) -> str:
    """Format user information for admin"""
    info = f"👤 Информация о пользователе\n\n"
    info += f"ID: {user.telegram_id}\n"
    info += f"Имя: {user.first_name or 'N/A'}\n"
    info += f"Фамилия: {user.last_name or 'N/A'}\n"
    info += f"Username: @{user.username or 'N/A'}\n"
    info += f"Телефон: {user.phone or 'Не указан'}\n\n"
    info += f"📊 Прогресс:\n"
    info += f"Визитов: {user.visits_count} / 9\n"
    info += f"Текущий цикл: {user.current_cycle}\n"
    
    if user.cycle_start_date:
        info += f"Начало цикла: {format_visit_date(user.cycle_start_date)}\n"
        info += f"Дней осталось: {user.get_days_remaining()}\n"
    
    info += f"\n🎁 Награда:\n"
    info += f"Доступна: {'Да' if user.reward_available else 'Нет'}\n"
    info += f"Сгенерирована: {'Да' if user.reward_generated else 'Нет'}\n"
    info += f"Использована: {'Да' if user.reward_used else 'Нет'}\n"
    
    return info


def format_stats(stats: dict) -> str:
    """Format statistics for admin"""
    text = "📊 Статистика программы лояльности\n\n"
    text += f"Всего участников: {stats['total_users']}\n"
    text += f"Активных участников: {stats['active_users']}\n"
    text += f"Выдано наград: {stats['rewards_issued']}\n"
    text += f"Завершённых циклов: {stats['completed_cycles']}"
    return text
