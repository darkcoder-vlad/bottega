from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_menu import get_main_keyboard

router = Router()

# Ссылка на политику конфиденциальности
POLICY_URL = "https://telegra.ph/Politika-konfidencialnosti-03-10-82"


@router.message(F.text == "📄 Политика конфиденциальности")
async def show_policy(message: Message):
    """Show privacy policy with inline button"""
    
    # Создаем инлайн-клавиатуру с ссылкой на политику
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📄 Читать политику конфиденциальности",
                url=POLICY_URL
            )
        ]
    ])
    
    await message.answer(
        "📄 <b>Политика конфиденциальности</b>\n\n"
        "Мы уважаем вашу конфиденциальность и защищаем ваши персональные данные.\n\n"
        "Нажмите кнопку ниже, чтобы ознакомиться с полной версией политики конфиденциальности:",
        reply_markup=inline_keyboard,
        parse_mode="HTML"
    )
