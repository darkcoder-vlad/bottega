from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.repositories import UserRepository, ShiftCodeRepository, RewardRepository
from bot.utils.formatters import format_user_info, format_stats
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(Command("setcode"))
async def cmd_setcode(message: Message, db):
    """Set shift code (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав для этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /setcode <код>\n"
            "Пример: /setcode 4831"
        )
        return
    
    code = args[1].strip()
    
    import re
    if not re.match(r'^\d{4}$', code):
        await message.answer(
            "❌ Код должен содержать 4 цифры.\n"
            "Пример: /setcode 4831"
        )
        return
    
    shift_repo = ShiftCodeRepository(db)
    shift_repo.set_code(code)
    
    await message.answer(
        f"✅ Код смены установлен: {code}\n\n"
        "Теперь гости могут использовать этот код для зачёта визитов."
    )


@router.message(Command("user"))
async def cmd_user(message: Message, db):
    """Get user info (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав для этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /user <телефон или ID>\n"
            "Пример: /user 79991234567"
        )
        return
    
    search_value = args[1].strip()
    user_repo = UserRepository(db)
    
    import re
    digits = re.sub(r'\D', '', search_value)
    if len(digits) == 11:
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        normalized_phone = f"+{digits}"
        user = user_repo.get_by_phone(normalized_phone)
    else:
        user = user_repo.get_by_telegram_id(search_value)
    
    if not user:
        await message.answer(f"❌ Пользователь не найден: {search_value}")
        return
    
    await message.answer(format_user_info(user))


@router.message(Command("stats"))
async def cmd_stats(message: Message, db):
    """Get statistics (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав для этой команды.")
        return
    
    user_repo = UserRepository(db)
    stats = user_repo.get_stats()
    
    await message.answer(format_stats(stats))


@router.message(Command("reward_used"))
async def cmd_reward_used(message: Message, db):
    """Mark reward as used (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав для этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /reward_used <код>\n"
            "Пример: /reward_used BTG-9384-KQ"
        )
        return
    
    code = args[1].strip().upper()
    reward_repo = RewardRepository(db)
    user_repo = UserRepository(db)
    
    reward = reward_repo.get_by_code(code)
    
    if not reward:
        await message.answer(f"❌ Награда не найдена: {code}")
        return
    
    if reward.is_used:
        await message.answer(f"ℹ️ Награда {code} уже была использована.")
        return
    
    reward_repo.mark_as_used(reward)
    
    user = user_repo.get_by_telegram_id(str(reward.user_id))
    if user:
        user_repo.reset_user_cycle(user)
    
    await message.answer(
        f"✅ Награда {code} отмечена как использованная.\n"
        f"Пользователь начал новый цикл."
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, db):
    """Broadcast message to all users (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав для этой команды.")
        return
    
    # Get message text (reply to a message or use argument)
    text_to_send = None
    
    if message.reply_to_message:
        text_to_send = message.reply_to_message.text or message.reply_to_message.caption
    else:
        args = message.text.split(maxsplit=1)
        if len(args) >= 2:
            text_to_send = args[1]
    
    if not text_to_send:
        await message.answer(
            "❌ Использование:\n"
            "1. Ответьте на сообщение командой /broadcast\n"
            "2. Или: /broadcast <текст сообщения>"
        )
        return
    
    user_repo = UserRepository(db)
    users = user_repo.get_all_active_users()
    
    sent_count = 0
    failed_count = 0
    
    await message.answer(f"📬 Начинаю рассылку {len(users)} пользователям...")
    
    # Split long messages into chunks (Telegram limit: 4096 chars)
    message_chunks = []
    chunk_size = 4000
    for i in range(0, len(text_to_send), chunk_size):
        message_chunks.append(text_to_send[i:i + chunk_size])
    
    for user in users:
        try:
            for chunk in message_chunks:
                await message.bot.send_message(
                    chat_id=user.telegram_id,
                    text=chunk,
                    parse_mode="HTML"
                )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to send to {user.telegram_id}: {e}")
    
    await message.answer(
        f"✅ Рассылка завершена.\n\n"
        f"Отправлено: {sent_count}\n"
        f"Не доставлено: {failed_count}"
    )
