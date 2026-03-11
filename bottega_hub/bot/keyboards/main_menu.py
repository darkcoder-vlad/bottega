from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Мой прогресс"),
                KeyboardButton(text="✅ Зачесть визит")
            ],
            [
                KeyboardButton(text="📜 Правила"),
                KeyboardButton(text="🎁 Моя награда")
            ],
            [
                KeyboardButton(text="📞 Поддержка")
            ],
            [
                KeyboardButton(text="📄 Политика конфиденциальности")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return keyboard


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for new users"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Зарегистрироваться", request_contact=True)]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with cancel button"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard
