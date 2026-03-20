from aiogram import Router, F
from aiogram.types import Message
import random
import string
from database.repositories import UserRepository, RewardRepository
from bot.keyboards.main_menu import get_main_keyboard
from config import VISITS_REQUIRED, MAX_REWARD_AMOUNT

router = Router()


def generate_reward_code() -> str:
    """Generate unique reward code in format BTG-XXXX-XX"""
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=2))
    return f"BTG-{part1}-{part2}"


@router.message(F.text == "🎁 Моя награда")
async def show_reward(message: Message, db):
    """Show reward status"""
    user_repo = UserRepository(db)
    reward_repo = RewardRepository(db)
    telegram_id = str(message.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        await message.answer(
            "⚠️ Вы ещё не зарегистрированы.\n"
            "Нажмите /start для начала участия."
        )
        return
    
    # Check if reward is available
    if not user.reward_available:
        visits = user.visits_count
        remaining = VISITS_REQUIRED - visits
        
        await message.answer(
            "🎁 Ваша награда\n\n"
            f"Ваш прогресс: {visits} из {VISITS_REQUIRED} визитов\n"
            f"До награды осталось: {remaining} визитов\n\n"
            "Накопите 9 визитов за 60 дней и получите 10-й визит бесплатно!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Check if reward already generated
    if user.reward_generated:
        reward = reward_repo.get_user_reward(user.id)
        
        if reward:
            if reward.is_used:
                await message.answer(
                    "🎁 Ваша награда\n\n"
                    f"Ваш код награды: {reward.reward_code}\n\n"
                    "✅ Награда уже использована.\n\n"
                    "Хотите начать новый цикл? Накопите ещё 9 визитов и получите новую награду!",
                    reply_markup=get_main_keyboard()
                )
            else:
                await message.answer(
                    "🎁 Ваша награда\n\n"
                    f"Ваш код награды: {reward.reward_code}\n\n"
                    "Покажите этот код официанту.\n"
                    f"Максимальная сумма: {MAX_REWARD_AMOUNT} ₽\n\n"
                    "⏰ Награда действительна до конца цикла (60 дней).",
                    reply_markup=get_main_keyboard()
                )
        return
    
    # Generate new reward
    reward_code = Reward.generate_code()
    reward = reward_repo.create(user.id, reward_code)
    user.reward_generated = True
    db.commit()
    
    await message.answer(
        "🎉 ПОЗДРАВЛЯЕМ! 🎉\n\n"
        f"Вы прошли BOTTEGA QUEST!\n"
        f"Выполнили {VISITS_REQUIRED} визитов за 60 дней!\n\n"
        "🎁 ВАШ КОД НАГРАДЫ:\n"
        f"```\n{reward_code}\n```\n\n"
        "Покажите этот код официанту.\n"
        f"Следующий визит будет бесплатным до {MAX_REWARD_AMOUNT} ₽.\n\n"
        "⏰ Награда действительна до конца цикла (60 дней).",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
