from aiogram import Router, F
from aiogram.types import Message
from database.repositories import UserRepository
from bot.keyboards.main_menu import get_main_keyboard
from config import BOT_NAME, VISITS_REQUIRED

router = Router()


def format_time_remaining(user) -> str:
    """Format time remaining with days, hours, minutes, seconds"""
    if not user.cycle_start_date:
        return "60 дней 0 часов 0 минут 0 секунд"
    
    from datetime import datetime, timedelta
    
    cycle_end = user.cycle_start_date + timedelta(days=60)
    now = datetime.utcnow()
    
    if now >= cycle_end:
        return "0 дней 0 часов 0 минут 0 секунд"
    
    remaining = cycle_end - now
    
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    seconds = remaining.seconds % 60
    
    # Simple declension
    def get_word(number, words):
        if number % 10 == 1 and number % 100 != 11:
            return words[0]
        elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
            return words[1]
        else:
            return words[2]
    
    day_word = get_word(days, ['день', 'дня', 'дней'])
    hour_word = get_word(hours, ['час', 'часа', 'часов'])
    minute_word = get_word(minutes, ['минута', 'минуты', 'минут'])
    second_word = get_word(seconds, ['секунда', 'секунды', 'секунд'])
    
    return f"{days} {day_word} {hours} {hour_word} {minutes} {minute_word} {seconds} {second_word}"


@router.message(F.text == "📊 Мой прогресс")
async def show_progress(message: Message, db):
    """Show user progress with timer"""
    user_repo = UserRepository(db)
    telegram_id = str(message.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        await message.answer(
            "⚠️ Вы ещё не зарегистрированы.\n"
            "Нажмите /start для начала участия."
        )
        return
    
    visits = user.visits_count
    remaining_visits = VISITS_REQUIRED - visits
    time_remaining = format_time_remaining(user)
    
    text = f"📊 <b>Ваш прогресс</b>\n\n"
    text += f"Визитов: {visits} из {VISITS_REQUIRED}\n"
    text += f"До награды осталось: {remaining_visits} визитов\n\n"
    text += f"⏰ <b>Времени осталось:</b>\n"
    text += f"<code>{time_remaining}</code>\n\n"
    
    if user.cycle_start_date:
        text += f"📅 Дата первого визита: {user.cycle_start_date.strftime('%d.%m.%Y')}\n"
        cycle_end_date = user.cycle_start_date.strftime('%d.%m.%Y')
        text += f"📅 Окончание цикла: {cycle_end_date}\n"
    
    if user.reward_available:
        text += "\n\n🎉 <b>Поздравляем! У вас доступна награда!</b>\n"
        text += "Перейдите в раздел 'Моя награда'"
    
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@router.message(F.text == "📜 Правила")
async def show_rules(message: Message):
    """Show program rules"""
    rules = (
        f"📜 <b>Правила программы лояльности {BOT_NAME}</b>\n\n"
        "1️⃣ <b>Регистрация</b>\n"
        "   Зарегистрируйтесь в боте, подтвердив номер телефона.\n\n"
        "2️⃣ <b>Как получить награду</b>\n"
        f"   • Посетите ресторан {VISITS_REQUIRED} раз за 60 дней\n"
        "   • Минимальная сумма чека: 3000 ₽\n"
        "   • Максимум 1 визит в сутки\n\n"
        "3️⃣ <b>Как зачесть визит</b>\n"
        "   • Нажмите 'Зачесть визит'\n"
        "   • Введите сумму чека\n"
        "   • Отправьте фото чека\n"
        "   • Дождитесь подтверждения администратора\n\n"
        "4️⃣ <b>Награда</b>\n"
        f"   • После {VISITS_REQUIRED} визитов вы получите 10-й бесплатный визит\n"
        "   • Награда действительна до конца цикла (60 дней)\n\n"
        "5️⃣ <b>Важно</b>\n"
        "   • Прогресс действует 60 дней с первого визита\n"
        "   • После использования награды цикл начинается заново\n"
        "   • Чек должен быть реальным (фото проверяется)\n"
        "   • При наличии бонусной карты, кешбек на чеки, участвующие в квесте, не начисляется\n\n"
        "❓ Вопросы? Напишите в поддержку."
    )
    await message.answer(rules, reply_markup=get_main_keyboard(), parse_mode="HTML")


@router.message(F.text == "📞 Поддержка")
async def show_support(message: Message):
    """Show support information"""
    support_text = (
        f"📞 <b>Поддержка {BOT_NAME}</b>\n\n"
        "По всем вопросам обращайтесь:\n\n"
        f"💬 Telegram: @bottega_gtn\n\n"
        "Мы работаем ежедневно с 10:00 до 22:00"
    )
    await message.answer(support_text, reply_markup=get_main_keyboard(), parse_mode="HTML")
