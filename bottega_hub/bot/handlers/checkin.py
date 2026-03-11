from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database.repositories import UserRepository, VisitRepository, ReceiptRepository
from bot.keyboards.main_menu import get_main_keyboard, get_cancel_keyboard
from bot.utils.validators import validate_amount
from config import MIN_CHECK_AMOUNT, VISITS_REQUIRED, ADMIN_IDS
import random

router = Router()


class ReceiptState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_photo = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


def get_receipt_keyboard(receipt_id: str) -> InlineKeyboardMarkup:
    """Create keyboard with confirm/reject buttons for admin"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"receipt_confirm_{receipt_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"receipt_reject_{receipt_id}")
        ]
    ])
    return keyboard


@router.message(F.text == "✅ Зачесть визит")
async def start_checkin(message: Message, state: FSMContext, db):
    """Start check-in process - amount + photo receipt"""
    user_repo = UserRepository(db)
    telegram_id = str(message.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    is_admin_user = is_admin(message.from_user.id)
    
    if not user:
        await message.answer(
            "⚠️ Вы ещё не зарегистрированы.\n"
            "Нажмите /start для начала участия."
        )
        return
    
    if not user.phone:
        await message.answer(
            "⚠️ Вы не подтвердили номер телефона.\n"
            "Нажмите /start для регистрации."
        )
        return
    
    # Check if already visited today (skip for admin)
    if not is_admin_user and not user.can_check_in_today():
        await message.answer(
            "⚠️ Вы уже засчитывали визит сегодня.\n"
            "Максимум 1 визит в сутки.\n\n"
            "Приходите завтра!"
        )
        return
    
    # Check if cycle expired (skip for admin)
    if not is_admin_user and user.is_cycle_expired() and user.visits_count > 0:
        await message.answer(
            "⏰ Срок действия вашего прогресса истёк (60 дней).\n"
            "Начинаем новый цикл!\n\n"
            "Накопите ещё 9 визитов и получите награду."
        )
        user_repo.reset_user_cycle(user)
    
    await state.set_state(ReceiptState.waiting_for_amount)
    await message.answer(
        f"💰 Введите сумму чека (от {MIN_CHECK_AMOUNT} ₽).\n\n"
        "После этого загрузите фото чека.\n\n"
        "Для отмены нажмите: ❌ Отмена",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ReceiptState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext, db):
    """Process check amount"""
    # Check for cancel
    if message.text and message.text.strip() == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Операция отменена.",
            reply_markup=get_main_keyboard()
        )
        return
    
    amount_str = message.text.strip() if message.text else ""
    is_valid, amount = validate_amount(amount_str)
    
    if not is_valid:
        await message.answer(
            f"❌ Неверная сумма.\n"
            f"Минимальная сумма чека: {MIN_CHECK_AMOUNT} ₽\n\n"
            "Попробуйте ещё раз (используйте точку или запятую):"
        )
        return
    
    # Store amount and move to photo
    await state.update_data(amount=amount)
    await state.set_state(ReceiptState.waiting_for_photo)
    
    await message.answer(
        f"✅ Сумма принята: {amount:.0f} ₽\n\n"
        "📸 Теперь отправьте фото чека.\n\n"
        "Для отмены нажмите: ❌ Отмена или отправьте текст 'Отмена'",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ReceiptState.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext, db):
    """Process receipt photo"""
    # Check for cancel first
    if message.text and message.text.strip() == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Операция отменена.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Check if it's a photo
    if not message.photo:
        await message.answer(
            "📸 Пожалуйста, отправьте фото чека.\n\n"
            "Для отмены нажмите: ❌ Отмена",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Get the best quality photo
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Get stored data
    data = await state.get_data()
    amount = data.get('amount')
    
    # Get user info
    user_repo = UserRepository(db)
    receipt_repo = ReceiptRepository(db)
    telegram_id = str(message.from_user.id)
    user = user_repo.get_by_telegram_id(telegram_id)
    is_admin_user = is_admin(message.from_user.id)
    
    # Double-check if already visited today (skip for admin)
    if not is_admin_user and not user.can_check_in_today():
        await message.answer(
            "⚠️ Вы уже засчитывали визит сегодня.\n"
            "Максимум 1 визит в сутки."
        )
        await state.clear()
        return
    
    # Generate receipt ID
    receipt_id = f"{user.telegram_id[-4:]}{random.randint(1000, 9999)}"
    
    # Get caption if any
    caption = message.caption
    
    # Create receipt in database
    receipt_repo.create(
        receipt_id=receipt_id,
        user_id=user.id,
        telegram_id=telegram_id,
        amount=amount,
        file_id=file_id,
        caption=caption
    )
    
    # Notify guest
    admin_note = " (режим админа: без лимитов)" if is_admin_user else ""
    await message.answer(
        f"✅ Чек принят{admin_note}!\n\n"
        f"💰 Сумма: {amount:.0f} ₽\n"
        f"🔢 Код проверки: {receipt_id}\n\n"
        "Ожидайте подтверждения от администратора.\n"
        "Вы получите уведомление."
    )
    
    # Notify admins
    visits_remaining = VISITS_REQUIRED - user.visits_count
    for admin_id in ADMIN_IDS:
        try:
            # Forward the photo to admin
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=f"🔔 <b>Новый чек на проверку</b>\n\n"
                        f"👤 Гость: {user.first_name or 'N/A'} {user.last_name or ''}\n"
                        f"📱 Телефон: <code>{user.phone or 'N/A'}</code>\n"
                        f"💰 Сумма: {amount:.0f} ₽\n"
                        f"📊 Прогресс: {user.visits_count} / {VISITS_REQUIRED} (осталось {visits_remaining})\n\n"
                        f"Проверьте чек и подтвердите:",
                reply_markup=get_receipt_keyboard(receipt_id),
                parse_mode="HTML"
            )
        except Exception as e:
            pass
    
    await state.clear()


@router.callback_query(F.data.startswith("receipt_confirm_"))
async def admin_confirm_receipt(callback: CallbackQuery, db):
    """Admin confirms the receipt"""
    receipt_id = callback.data.split("_")[2]
    
    receipt_repo = ReceiptRepository(db)
    user_repo = UserRepository(db)
    visit_repo = VisitRepository(db)
    
    # Get receipt
    receipt = receipt_repo.get_by_receipt_id(receipt_id)
    
    if not receipt:
        await callback.answer("❌ Чек не найден или уже обработан", show_alert=True)
        return
    
    # Confirm receipt
    receipt_repo.confirm(receipt, str(callback.from_user.id))
    
    # Get user and add visit
    user = user_repo.get_by_telegram_id(receipt.telegram_id)
    if user:
        visit_repo.create(user.id, receipt.amount, receipt_id)
        user = user_repo.add_visit(user, receipt.amount)
        
        visits = user.visits_count
        remaining = VISITS_REQUIRED - visits
        
        # Notify guest
        try:
            await callback.bot.send_message(
                chat_id=receipt.telegram_id,
                text=f"✅ <b>Визит подтверждён!</b>\n\n"
                     f"💰 Сумма: {receipt.amount:.0f} ₽\n"
                     f"📊 Прогресс: {visits} / {VISITS_REQUIRED}\n"
                     f"До награды осталось: {remaining} визитов\n\n"
                     "Спасибо за визит!",
                reply_markup=get_main_keyboard()
            )
        except:
            pass
        
        # Check if reward available
        if user.reward_available and not user.reward_generated:
            try:
                await callback.bot.send_message(
                    chat_id=receipt.telegram_id,
                    text=f"🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
                         f"Вы прошли BOTTEGA QUEST!\n"
                         f"Выполнили {VISITS_REQUIRED} визитов за 60 дней!\n\n"
                         "Ваш следующий визит будет бесплатным до 3000 ₽.\n\n"
                         "Перейдите в раздел 'Моя награда', чтобы получить код.",
                    reply_markup=get_main_keyboard()
                )
            except:
                pass
    
    # Update admin message
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ <b>Подтверждено</b>",
        parse_mode="HTML"
    )
    
    await callback.answer("✅ Визит подтверждён!", show_alert=True)


@router.callback_query(F.data.startswith("receipt_reject_"))
async def admin_reject_receipt(callback: CallbackQuery, db):
    """Admin rejects the receipt"""
    receipt_id = callback.data.split("_")[2]
    
    receipt_repo = ReceiptRepository(db)
    
    # Get receipt
    receipt = receipt_repo.get_by_receipt_id(receipt_id)
    
    if not receipt:
        await callback.answer("❌ Чек не найден или уже обработан", show_alert=True)
        return
    
    # Reject receipt
    receipt_repo.reject(receipt)
    
    # Notify guest
    try:
        await callback.bot.send_message(
            chat_id=receipt.telegram_id,
            text=f"❌ <b>Чек отклонён</b>\n\n"
                 f"Сумма: {receipt.amount:.0f} ₽\n\n"
                 "Пожалуйста, обратитесь к администратору.",
            reply_markup=get_main_keyboard()
        )
    except:
        pass
    
    # Update admin message
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ <b>Отклонено</b>",
        parse_mode="HTML"
    )
    
    await callback.answer("❌ Чек отклонён", show_alert=True)
