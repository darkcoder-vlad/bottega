import logging
import os
import shutil
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.database import get_session
from database.repositories import UserRepository
from config import INACTIVE_DAYS_NOTIFY, VISITS_REQUIRED

logger = logging.getLogger(__name__)


async def create_database_backup():
    """Создать резервную копию базы данных"""
    try:
        # Пути
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'data', 'bottega.db')
        backup_dir = os.path.join(base_dir, 'backups')
        retention_days = 7
        
        # Создаём папку для бэкапов
        os.makedirs(backup_dir, exist_ok=True)
        
        # Проверяем существование базы
        if not os.path.exists(db_path):
            logger.warning("Database not found for backup")
            return
        
        # Имя файла с датой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'bottega_backup_{timestamp}.db')
        
        # Копируем базу
        shutil.copy2(db_path, backup_file)
        
        # Получаем размер
        db_size = os.path.getsize(db_path)
        backup_size = os.path.getsize(backup_file)
        
        logger.info(f"✅ Database backup created: {backup_file} ({backup_size} bytes)")
        
        # Удаляем старые бэкапы
        cleanup_old_backups(backup_dir, retention_days)
        
    except Exception as e:
        logger.error(f"Backup error: {e}")


def cleanup_old_backups(backup_dir, retention_days):
    """Удалить бэкапы старше retention_days дней"""
    try:
        if not os.path.exists(backup_dir):
            return
        
        deleted_count = 0
        for filename in os.listdir(backup_dir):
            if filename.startswith('bottega_backup_') and filename.endswith('.db'):
                filepath = os.path.join(backup_dir, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                age = datetime.now() - file_mtime
                
                if age.days > retention_days:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"🗑️ Deleted old backup: {filename}")
        
        if deleted_count > 0:
            logger.info(f"📋 Deleted {deleted_count} old backup(s)")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


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

    # Create database backup daily at 03:00
    scheduler.add_job(
        create_database_backup,
        CronTrigger(hour=3, minute=0),
        id='database_backup'
    )

    scheduler.start()
    logger.info("Notification scheduler started")

    return scheduler
