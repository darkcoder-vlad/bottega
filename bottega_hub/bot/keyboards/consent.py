from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_consent_keyboard(policy_url: str = "#") -> InlineKeyboardMarkup:
    """Keyboard for consent screen"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Читать политику конфиденциальности", url=policy_url)
        ],
        [
            InlineKeyboardButton(text="✅ Я согласен", callback_data="consent_accept")
        ]
    ])
    return keyboard
