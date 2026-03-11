from aiogram import Router, F
from aiogram.types import Message, Contact, CallbackQuery
from aiogram.filters import CommandStart
from database.repositories import UserRepository, ConsentRepository
from bot.keyboards.main_menu import get_main_keyboard, get_start_keyboard
from bot.keyboards.consent import get_consent_keyboard
from config import BOT_NAME, VISITS_REQUIRED, CYCLE_DAYS, MAX_REWARD_AMOUNT

router = Router()

# Ссылка на политику конфиденциальности
POLICY_URL = "https://telegra.ph/Politika-konfidencialnosti-03-10-82"


@router.message(CommandStart())
async def cmd_start(message: Message, db):
    """Handle /start command"""
    user_repo = UserRepository(db)
    consent_repo = ConsentRepository(db)
    telegram_id = str(message.from_user.id)
    
    # Check if user has accepted consent
    if consent_repo.has_accepted(telegram_id):
        # User already accepted, check if registered
        user = user_repo.get_by_telegram_id(telegram_id)
        if user and user.phone:
            # Fully registered, show main menu
            await message.answer(
                f"👋 С возвращением, {user.first_name or 'друг'}!\n\n"
                f"Добро пожаловать в {BOT_NAME}!\n"
                "Выберите действие в меню:",
                reply_markup=get_main_keyboard()
            )
        else:
            # Consent accepted, but no phone - ask for phone
            await message.answer(
                f"✅ <b>Согласие принято!</b>\n\n"
                "Чтобы начать участие в квесте, зарегистрируйте свой номер телефона:",
                reply_markup=get_start_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # First time - show promo and consent
    await message.answer(
        f"👋 <b>Добро пожаловать в БОТТЕГА квест!</b>\n\n"
        
        f"🎁 <b>9 визитов за 60 дней → 10-й визит бесплатно</b>\n\n"
        
        f"📋 <b>Как это работает:</b>\n"
        f"• За каждый визит с чеком от 3000 ₽ получайте отметку\n"
        f"• Нужно собрать {VISITS_REQUIRED} визитов\n"
        f"• Ваш {VISITS_REQUIRED + 1}-й визит будет бесплатным\n\n"
        
        "*подробно обо всех правилах в меню\n\n"
        
        "Чтобы начать участие, следуйте дальнейшим шагам.\n\n"
        
        "📄 <b>Политика конфиденциальности:</b>\n"
        "Для участия необходимо согласие на обработку персональных данных.\n"
        "Нажмите кнопку ниже, чтобы прочитать и принять:",
        
        reply_markup=get_consent_keyboard(POLICY_URL),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "consent_accept")
async def consent_accept(callback: CallbackQuery, db):
    """Handle consent acceptance"""
    consent_repo = ConsentRepository(db)
    user_repo = UserRepository(db)
    telegram_id = str(callback.from_user.id)
    
    # Get or create consent
    consent = consent_repo.get_by_telegram_id(telegram_id)
    if not consent:
        consent = consent_repo.create(telegram_id)
    
    # Accept consent
    consent_repo.accept(consent)
    
    # Check if user exists and has phone
    user = user_repo.get_by_telegram_id(telegram_id)
    
    if user and user.phone:
        # Already registered
        await callback.message.answer(
            f"✅ <b>Согласие принято!</b>\n\n"
            f"Добро пожаловать в {BOT_NAME}!\n"
            "Выберите действие в меню:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Need to register phone - show start keyboard with phone button
        await callback.message.answer(
            f"✅ <b>Согласие принято!</b>\n\n"
            "Чтобы начать участие в квесте, зарегистрируйте свой номер телефона:",
            reply_markup=get_start_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.message(F.contact)
async def handle_contact(message: Message, db):
    """Handle phone contact"""
    user_repo = UserRepository(db)
    consent_repo = ConsentRepository(db)
    telegram_id = str(message.from_user.id)
    
    # Check if consent accepted
    if not consent_repo.has_accepted(telegram_id):
        await message.answer(
            "⚠️ Сначала необходимо принять согласие на обработку данных.\n"
            "Нажмите /start"
        )
        return
    
    # Check if user already registered
    existing_user = user_repo.get_by_telegram_id(telegram_id)
    if existing_user and existing_user.phone:
        await message.answer(
            f"✅ Вы уже зарегистрированы!\n\n"
            f"Ваш номер: {existing_user.phone}\n\n"
            "Выберите действие в меню:",
            reply_markup=get_main_keyboard()
        )
        return
    
    contact = message.contact
    phone = contact.phone_number
    
    # Normalize phone
    import re
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('7'):
        normalized_phone = f"+{digits}"
    else:
        normalized_phone = phone
    
    # Check if phone already registered
    existing_user_by_phone = user_repo.get_by_phone(normalized_phone)
    if existing_user_by_phone:
        await message.answer(
            "⚠️ Этот номер телефона уже зарегистрирован в системе.\n"
            "Если это ваш номер, пожалуйста, войдите с того же Telegram аккаунта."
        )
        return
    
    # Create new user
    user = user_repo.create(
        telegram_id=telegram_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Update phone
    user_repo.update_phone(user, normalized_phone)
    
    # Link consent to user
    consent = consent_repo.get_by_telegram_id(telegram_id)
    if consent:
        consent.user_id = user.id
        db.commit()
    
    await message.answer(
        f"✅ {user.first_name or 'Участник'}, вы успешно зарегистрированы!\n\n"
        f"Ваш номер: {normalized_phone}\n\n"
        f"🎁 Ваша цель: {VISITS_REQUIRED} визитов за {CYCLE_DAYS} дней\n"
        f"🎁 Награда: 10-й визит бесплатно\n\n"
        "Выберите действие в меню:",
        reply_markup=get_main_keyboard()
    )
