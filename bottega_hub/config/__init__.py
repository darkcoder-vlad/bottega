import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Admin IDs
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bottega_hub/data/bottega.db')

# Loyalty Program Settings
MIN_CHECK_AMOUNT = int(os.getenv('MIN_CHECK_AMOUNT', '3000'))
VISITS_REQUIRED = int(os.getenv('VISITS_REQUIRED', '9'))
CYCLE_DAYS = int(os.getenv('CYCLE_DAYS', '60'))
MAX_REWARD_AMOUNT = int(os.getenv('MAX_REWARD_AMOUNT', '3000'))

# Notifications
INACTIVE_DAYS_NOTIFY = int(os.getenv('INACTIVE_DAYS_NOTIFY', '7'))

# Bot name
BOT_NAME = "БОТТЕГА квест"
