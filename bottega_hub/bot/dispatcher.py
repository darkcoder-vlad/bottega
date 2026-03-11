import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables FIRST (before any other imports)
# Go up TWO levels from bot/dispatcher.py to reach project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path, override=True)
print(f"Loaded .env from: {env_path}")
print(f"ADMIN_IDS from os.getenv: {os.getenv('ADMIN_IDS')}")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from database.database import init_db
from bot.handlers import (
    start_router, menu_router, progress_router, checkin_router,
    reward_router, rules_router, support_router, policy_router, admin_router, callback_router
)
from bot.middlewares import DatabaseMiddleware, LoggingMiddleware
from bot.notifications import setup_scheduler

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, 'bot.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Called on bot startup"""
    logger.info("Bot starting up...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Setup scheduler
    scheduler = setup_scheduler(bot)
    dispatcher.scheduler = scheduler
    
    # Log bot info
    me = await bot.get_me()
    logger.info(f"Bot @{me.username} started")
    logger.info(f"Admin IDs: {ADMIN_IDS}")


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Called on bot shutdown"""
    logger.info("Bot shutting down...")
    
    # Stop scheduler
    if hasattr(dispatcher, 'scheduler'):
        dispatcher.scheduler.shutdown()
    
    await bot.session.close()


def create_dispatcher() -> Dispatcher:
    """Create and configure dispatcher"""
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    
    # Register startup/shutdown handlers
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    
    # Setup middlewares
    dispatcher.message.middleware(DatabaseMiddleware())
    dispatcher.message.middleware(LoggingMiddleware())
    dispatcher.callback_query.middleware(DatabaseMiddleware())
    dispatcher.callback_query.middleware(LoggingMiddleware())
    
    # Include routers
    dispatcher.include_routers(
        start_router,
        menu_router,
        progress_router,
        checkin_router,
        reward_router,
        rules_router,
        support_router,
        policy_router,
        admin_router,
        callback_router
    )
    
    return dispatcher


async def start_bot():
    """Start bot polling"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found. Please set it in .env file.")
        sys.exit(1)
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dispatcher = create_dispatcher()
    
    try:
        await dispatcher.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(start_bot())
