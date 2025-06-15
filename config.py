TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # <-- Set your token here

DB_URI = "sqlite+aiosqlite:///bot/database/db.sqlite3"  # SQLite for dev, change to Postgres in prod

ADMIN_IDS = [123456789]  # Telegram user IDs of admins
TASK_TIMEOUT_MINUTES = 20
MAX_VIDEO_COUNT = 5
MAX_VIDEO_DURATION = 5 * 60  # seconds