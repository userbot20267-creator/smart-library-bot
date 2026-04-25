"""مهمة النسخ الاحتياطي اليومي"""
import logging
import datetime
from telegram.ext import ContextTypes
from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def daily_backup(context: ContextTypes.DEFAULT_TYPE):
    """نسخ احتياطي يومي لقاعدة البيانات"""
    try:
        logger.info("Starting daily backup...")

        # إذا كانت PostgreSQL، يمكن استخدام pg_dump
        # إذا كانت SQLite، ننسخ الملف

        if "sqlite" in settings.DATABASE_URL:
            import shutil
            backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy("library.db", f"/tmp/{backup_name}")

            # إرسال للقناة الاحتياطية
            if settings.BACKUP_CHANNEL_ID:
                with open(f"/tmp/{backup_name}", "rb") as f:
                    await context.bot.send_document(
                        chat_id=settings.BACKUP_CHANNEL_ID,
                        document=f,
                        caption=f"📦 نسخة احتياطية - {datetime.datetime.now().strftime('%Y-%m-%d')}"
                    )

        logger.info("Daily backup completed")
    except Exception as e:
        logger.error(f"Backup error: {e}")
