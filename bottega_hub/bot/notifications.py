import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.database import get_session
from database.repositories import UserRepository
from config import INACTIVE_DAYS_NOTIFY, VISITS_REQUIRED

logger = logging.getLogger(__name__)


async def send_inactive_notifications(bot):
    """Send notifications to inactive users"""
    db = get_session()
    try:
        user_repo = UserRepository(db)
        users = user_repo.get_users_for_notification(INACTIVE_DAYS_NOTIFY)
        
        sent_count = 0
        for user in users:
            try:
                visits = user.visits_count
                remaining = VISITS_REQUIRED - visits
                
                message = (
                    f"👋 {user.first_name or 'Друг'}, мы скучаем!\n\n"
                    f"Вы на {visits} / {VISITS_REQUIRED} визитов.\n"
                    f"До бесплатного ужина осталось всего {remaining} визитов.\n\n"
                    "Приходите к нам снова и продолжайте копить визиты!\n\n"
                    "Ждём вас в БОТТЕГА квест!"
                )
                
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification to {user.telegram_id}: {e}")
        
        if sent_count > 0:
            logger.info(f"Sent {sent_count} inactive notifications")
    finally:
        db.close()


async def check_cycle_expirations(bot):
    """Check and notify about cycle expirations"""
    db = get_session()
    try:
        user_repo = UserRepository(db)
        users = user_repo.get_all_active_users()
        
        for user in users:
            if user.cycle_start_date and user.get_days_remaining() <= 3:
                # User has less than 3 days left in cycle
                try:
                    message = (
                        f"⏰ {user.first_name or 'Друг'}, у вас осталось мало времени!\n\n"
                        f"До конца цикла осталось {user.get_days_remaining()} дней.\n"
                        f"Ваш прогресс: {user.visits_count} / {VISITS_REQUIRED}\n\n"
                        "Успейте получить награду!"
                    )
                    
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message
                    )
                except Exception as e:
                    logger.error(f"Failed to send expiration warning to {user.telegram_id}: {e}")
    finally:
        db.close()


def setup_scheduler(bot):
    """Setup notification scheduler"""
    scheduler = AsyncIOScheduler()
    
    # Send inactive notifications daily at 18:00
    scheduler.add_job(
        send_inactive_notifications,
        CronTrigger(hour=18, minute=0),
        args=[bot],
        id='inactive_notifications'
    )
    
    # Check cycle expirations daily at 10:00
    scheduler.add_job(
        check_cycle_expirations,
        CronTrigger(hour=10, minute=0),
        args=[bot],
        id='cycle_expirations'
    )
    
    scheduler.start()
    logger.info("Notification scheduler started")
    
    return scheduler
