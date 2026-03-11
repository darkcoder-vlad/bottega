from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_consent_inline(policy_url: str = "#") -> InlineKeyboardMarkup:
    """Inline keyboard for consent screen (deprecated - use consent.py)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Читать политику конфиденциальности", url=policy_url)
        ],
        [
            InlineKeyboardButton(text="✅ Я согласен", callback_data="consent_accept")
        ]
    ])
    return keyboard
