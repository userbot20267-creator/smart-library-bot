"""التقارير الأسبوعية"""
import logging
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import User, Book, Download
from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
    """تقرير أسبوعي للمالك"""
    try:
        db: Session = context.bot_data.get("db_session")
        if not db:
            return

        # إحصائيات الأسبوع
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)

        new_users = db.query(User).filter(User.created_at >= week_ago).count()
        new_downloads = db.query(Download).filter(Download.downloaded_at >= week_ago).count()
        total_books = db.query(Book).count()
        total_users = db.query(User).count()

        # أكثر الكتب تحميلاً هذا الأسبوع
        top_books = db.query(Book).order_by(Book.download_count.desc()).limit(5).all()

        report = f"""
📊 <b>التقرير الأسبوعي</b>

📅 الفترة: آخر 7 أيام

👥 مستخدمين جدد: {new_users}
📥 تحميلات جديدة: {new_downloads}
📚 إجمالي الكتب: {total_books}
👤 إجمالي المستخدمين: {total_users}

🏆 <b>أكثر الكتب تحميلاً:</b>
"""
        for i, book in enumerate(top_books, 1):
            # تم تصحيح السطر أدناه بإضافة علامة التنصيص وإضافة \n للسطر الجديد
            report += f"\n{i}. {book.title} ({book.download_count})"

        # إرسال للمالك
        await context.bot.send_message(
            settings.OWNER_ID,
            report,
            parse_mode="HTML"
        )

        logger.info("Weekly report sent")
    except Exception as e:
        logger.error(f"Weekly report error: {e}")
        
