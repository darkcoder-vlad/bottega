from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import logging
from database.repositories import UserRepository, ShiftCodeRepository, RewardRepository, VisitRepository
from bot.utils.formatters import format_user_info, format_stats
from config import ADMIN_IDS, MIN_CHECK_AMOUNT
from datetime import datetime

logger = logging.getLogger(__name__)

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


@router.message(Command("add_visit"))
async def cmd_add_visit(message: Message, db):
    """Добавить визит пользователю по номеру телефона (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет прав для этой команды.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /add_visit <телефон> [сумма чека]\n"
            "Пример: /add_visit 79991234567 5000\n"
            "Или: /add_visit +79991234567"
        )
        return

    # Parse phone and amount
    parts = args[1].split()
    phone = parts[0].strip()
    
    # Default amount or from argument
    amount = MIN_CHECK_AMOUNT
    if len(parts) >= 2:
        try:
            amount = int(parts[1])
        except ValueError:
            await message.answer("❌ Сумма чека должна быть числом.")
            return

    user_repo = UserRepository(db)
    visit_repo = VisitRepository(db)

    # Normalize phone
    import re
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11:
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        normalized_phone = f"+{digits}"
    else:
        normalized_phone = f"+{digits}"

    user = user_repo.get_by_phone(normalized_phone)

    if not user:
        await message.answer(f"❌ Пользователь не найден: {phone}")
        return

    # Check if user already has a visit today
    today = datetime.now().date()
    existing_visits = visit_repo.get_user_visits(user.id)
    
    has_visit_today = False
    for visit in existing_visits:
        if visit.visit_date and visit.visit_date.date() == today:
            has_visit_today = True
            break

    if has_visit_today:
        await message.answer(
            f"⚠️ У пользователя уже есть визит сегодня.\n\n"
            f"Пользователь: {user.first_name} {user.last_name or ''}\n"
            f"Телефон: {user.phone}\n"
            f"Всего визитов: {user.visits_count}"
        )
        return

    # Create visit record
    visit_repo.create(
        user_id=user.id,
        check_amount=amount,
        status='approved'  # Auto-approve for admin
    )

    # Update user visits count using add_visit method
    user_repo.add_visit(user, amount)
    
    # Refresh user data from DB
    updated_user = user_repo.get_by_telegram_id(str(user.telegram_id))
    new_visits_count = updated_user.visits_count

    # Check if cycle completed (9 visits reached)
    from bot.handlers.reward import generate_reward_code
    reward_repo = RewardRepository(db)
    
    if new_visits_count >= 9 and not updated_user.reward_available:
        reward_code = generate_reward_code()
        reward_repo.create(
            user_id=updated_user.id,
            reward_code=reward_code,
            amount=MIN_CHECK_AMOUNT
        )
        
        # Mark reward as available
        updated_user.reward_available = True
        user_repo.db.commit()
        
        # Notify user
        try:
            await message.bot.send_message(
                chat_id=updated_user.telegram_id,
                text=(
                    f"🎉 Поздравляем! Вы завершили цикл!\n\n"
                    f"Ваш код награды: <code>{reward_code}</code>\n\n"
                    f"Покажите этот код официанту для получения бесплатного блюда.\n\n"
                    f"Спасибо, что вы с нами!"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user about reward: {e}")

    remaining = max(0, 9 - new_visits_count)
    
    await message.answer(
        f"✅ Визит добавлен!\n\n"
        f"Пользователь: {updated_user.first_name} {updated_user.last_name or ''}\n"
        f"Телефон: {updated_user.phone}\n"
        f"Сумма чека: {amount} ₽\n"
        f"Всего визитов: {new_visits_count}\n"
        f"До награды осталось: {remaining}"
    )
