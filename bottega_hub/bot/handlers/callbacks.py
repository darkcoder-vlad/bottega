from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from database.repositories import UserRepository
from bot.utils.formatters import format_progress
from config import VISITS_REQUIRED

router = Router()


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """Handle back to menu callback"""
    from bot.keyboards.main_menu import get_main_keyboard
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "show_progress")
async def callback_show_progress(callback: CallbackQuery, db):
    """Handle show progress callback"""
    user_repo = UserRepository(db)
    telegram_id = str(callback.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    
    visits = user.visits_count
    days_remaining = user.get_days_remaining()
    
    text = format_progress(visits, VISITS_REQUIRED, days_remaining)
    
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "progress_details")
async def callback_progress_details(callback: CallbackQuery, db):
    """Handle progress details callback"""
    user_repo = UserRepository(db)
    telegram_id = str(callback.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    
    details = f"📊 Детали прогресса\n\n"
    details += f"Визитов: {user.visits_count} / {VISITS_REQUIRED}\n"
    details += f"Осталось: {VISITS_REQUIRED - user.visits_count} визитов\n"
    details += f"Дней осталось: {user.get_days_remaining()}\n"
    
    if user.cycle_start_date:
        details += f"Начало цикла: {user.cycle_start_date.strftime('%d.%m.%Y')}"
    
    await callback.message.edit_text(details)
    await callback.answer()


@router.callback_query(F.data == "get_reward")
async def callback_get_reward(callback: CallbackQuery, db):
    """Handle get reward callback"""
    user_repo = UserRepository(db)
    from database.repositories import RewardRepository
    
    telegram_id = str(callback.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    
    if not user.reward_available:
        await callback.answer("Награда ещё не доступна", show_alert=True)
        return
    
    if user.reward_generated:
        reward_repo = RewardRepository(db)
        reward = reward_repo.get_user_reward(user.id)
        if reward:
            await callback.answer(f"Ваш код: {reward.reward_code}", show_alert=True)
        return
    
    await callback.answer("Перейдите в раздел 'Моя награда'", show_alert=True)
