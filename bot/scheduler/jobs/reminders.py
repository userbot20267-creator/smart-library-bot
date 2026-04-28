"""تذكيرات المستخدمين"""
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import User, Download, Rating
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def rating_reminders(context: ContextTypes.DEFAULT_TYPE):
    """تذكير المستخدمين بتقييم الكتب"""
    try:
        db: Session = context.bot_data.get("db_session")
        if not db:
            return

        # البحث عن تحميلات منذ 48 ساعة بدون تقييم
        two_days_ago = datetime.now() - timedelta(hours=48)

        downloads = db.query(Download).filter(
            Download.downloaded_at <= two_days_ago
        ).all()

        for download in downloads:
            # التحقق من عدم وجود تقييم
            existing_rating = db.query(Rating).filter(
                Rating.user_id == download.user_id,
                Rating.book_id == download.book_id
            ).first()

            if not existing_rating:
                try:
                    await context.bot.send_message(
                        download.user_id,
                        f"""
💬 <b>ما رأيك في الكتاب؟</b>

📖 {download.book.title if download.book else 'كتاب'}

هل تريد تقييمه؟ ⭐
""",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⭐ تقييم", callback_data=f"rate_{download.book_id}")],
                            [InlineKeyboardButton("❌ لاحقاً", callback_data="dismiss_reminder")]
                        ])
                    )
                except Exception as e:
                    logger.error(f"Reminder error: {e}")

        logger.info("Rating reminders sent")
    except Exception as e:
        logger.error(f"Reminders error: {e}")
