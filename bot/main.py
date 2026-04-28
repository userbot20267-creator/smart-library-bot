"""ملف تشغيل البوت الرئيسي - النسخة المصححة والمحدثة"""
import asyncio
import logging
import os
import sys

# إضافة المسار لضمان استيراد الوحدات بشكل صحيح
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import get_settings
from bot.database.models import Database
from bot.middlewares import rate_limit_middleware
from bot.handlers import *
from bot.features import *
from bot.scheduler import daily_backup, weekly_report, rating_reminders

# إعداد Logging لمراقبة الأداء والأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout  # ✅ توجيه السجلات إلى stdout (لحل مشكلة severity: error في Railway)
)
logger = logging.getLogger(__name__)

settings = get_settings()

# --- إصلاح ربط قاعدة البيانات لـ PostgreSQL ---
db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
if db_url and db_url.startswith("postgres://"):
    # تصحيح الروابط القديمة لـ Postgres لتتوافق مع SQLAlchemy
    db_url = db_url.replace("postgres://", "postgresql://", 1)

db = Database(db_url)
db.create_tables()

# ✅ إضافة معالج الأخطاء العام
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأخطاء غير المتوقعة"""
    logger.error(f"Update {update} caused error: {context.error}")

# حفظ الجلسة والمعلومات الحساسة في bot_data لضمان توفرها للميزات
async def post_init(application: Application):
    """التشغيل الأولي وحقن الإعدادات الحية"""
    application.bot_data["db_session"] = db.SessionLocal()
    
    # ضمان قراءة OWNER_ID كـ رقم صحيح من Railway مباشرة
    owner_id_raw = os.getenv("OWNER_ID", settings.OWNER_ID)
    try:
        application.bot_data["owner_id"] = int(owner_id_raw)
    except (ValueError, TypeError):
        application.bot_data["owner_id"] = 0
        
    logger.info(f"✅ Bot initialized. Admin ID recognized: {application.bot_data['owner_id']}")


async def post_shutdown(application: Application):
    """إغلاق الموارد عند إيقاف البوت"""
    if "db_session" in application.bot_data:
        application.bot_data["db_session"].close()
    logger.info("🛑 Bot shutdown")


# Middleware wrapper لتطبيق قيود معدل الرسائل
async def middleware_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تطبيق middlewares"""
    if not await rate_limit_middleware(update, context):
        return False
    return True


async def main():  # ✅ تحويل main إلى async للتعامل مع await
    """الدالة الرئيسية لتشغيل البوت"""
    logger.info("🚀 Starting Smart Library Bot...")

    # إنشاء تطبيق التليجرام
    application = Application.builder().token(settings.BOT_TOKEN).build()

    # ✅ تسجيل معالج الأخطاء
    application.add_error_handler(error_handler)

    # ربط دوال البداية والنهاية
    application.post_init = post_init
    application.post_shutdown = post_shutdown

    # ========== معالجات الأوامر (Command Handlers) ==========

    # أوامر المستخدم العام
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("me", profile_command))
    application.add_handler(CommandHandler("referral", referral_command))

    # أوامر المشرف (Admin)
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("ai_search", ai_search_command))
    application.add_handler(CommandHandler("ai_insights", ai_insights_command))
    application.add_handler(CommandHandler("batch", batch_upload_start))

    # ========== معالجات المحادثة (Conversation Handlers) ==========

    # ✅ تم تصحيح per_message إلى False لأن المحادثة تحتوي على MessageHandler وCommandHandler
    search_conv = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))],
        per_message=False
    )
    application.add_handler(search_conv)

    # إضافة كتاب جديد
    add_book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_book_start, pattern="^admin_add_book$")],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_title)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_author)],
            3: [CallbackQueryHandler(add_book_category, pattern="^selcat_")],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_description)],
            5: [MessageHandler(filters.Document.PDF | filters.TEXT, add_book_file)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))],
        per_chat=True
    )
    application.add_handler(add_book_conv)

    # الرفع الدفعي للملفات
    batch_conv = ConversationHandler(
        entry_points=[CommandHandler("batch", batch_upload_start)],
        states={
            1: [MessageHandler(filters.Document.PDF, collect_batch_files)],
            2: [CallbackQueryHandler(batch_select_category, pattern="^batchcat_")],
            3: [CallbackQueryHandler(batch_select_author, pattern="^batchauth_")]
        },
        fallbacks=[
            CommandHandler("done", batch_done),
            CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))
        ],
        per_chat=True
    )
    application.add_handler(batch_conv)

    # ✅ تم تصحيح per_message إلى False
    comment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_comment_start, pattern="^add_comment_")],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_comment)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))],
        per_message=False
    )
    application.add_handler(comment_conv)

    # ========== معالجات الأزرار (Callback Query Handlers) ==========

    # القائمة الرئيسية والتصفح
    application.add_handler(CallbackQueryHandler(browse_categories, pattern="^browse_categories$"))
    application.add_handler(CallbackQueryHandler(smart_search_callback, pattern="^smart_search$"))
    application.add_handler(CallbackQueryHandler(my_favorites, pattern="^my_favorites$"))
    application.add_handler(CallbackQueryHandler(my_downloads, pattern="^my_downloads$"))
    application.add_handler(CallbackQueryHandler(show_leaderboard, pattern="^leaderboard$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: start_command(u, c), pattern="^main_menu$"))

    # تفاصيل الكتب والعمليات
    application.add_handler(CallbackQueryHandler(show_category_books, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(show_book_details, pattern="^book_"))
    application.add_handler(CallbackQueryHandler(download_book, pattern="^download_"))
    application.add_handler(CallbackQueryHandler(toggle_favorite, pattern="^fav_|^unfav_"))
    application.add_handler(CallbackQueryHandler(rate_book, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(share_book, pattern="^share_"))
    application.add_handler(CallbackQueryHandler(similar_books, pattern="^similar_"))
    application.add_handler(CallbackQueryHandler(ai_summary, pattern="^ai_summary_"))
    application.add_handler(CallbackQueryHandler(ai_assistant, pattern="^ai_assist_"))

    # التعليقات والإشعارات
    application.add_handler(CallbackQueryHandler(show_comments, pattern="^comments_"))
    application.add_handler(CallbackQueryHandler(like_comment, pattern="^like_comment_"))
    application.add_handler(CallbackQueryHandler(notification_settings, pattern="^notification_settings$"))
    application.add_handler(CallbackQueryHandler(toggle_notification, pattern="^toggle_notify_"))

    # المشرف - لوحة التحكم
    application.add_handler(CallbackQueryHandler(admin_books, pattern="^admin_books$"))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(admin_users, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(list_all_books, pattern="^admin_list_books$"))
    application.add_handler(CallbackQueryHandler(advanced_search_books, pattern="^admin_advanced_search$"))
    application.add_handler(CallbackQueryHandler(ai_recategorize, pattern="^admin_ai_recategorize$"))
    application.add_handler(CallbackQueryHandler(generate_description_for_existing, pattern="^admin_ai_desc$"))
    application.add_handler(CallbackQueryHandler(save_ai_description, pattern="^save_desc_"))
    application.add_handler(CallbackQueryHandler(confirm_ai_add, pattern="^ai_add_|^cancel_ai_search$"))
    application.add_handler(CallbackQueryHandler(batch_confirm_upload, pattern="^batch_confirm$|^batch_cancel$"))

    # ========== الجدولة التلقائية (Scheduler) ==========
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_backup, "cron", hour=3, minute=0, args=[application])
    scheduler.add_job(weekly_report, "cron", day_of_week="sun", hour=9, minute=0, args=[application])
    scheduler.add_job(rating_reminders, "cron", hour=18, minute=0, args=[application])
    scheduler.start()

    # ========== تشغيل البوت (Webhook vs Polling) ==========
    # ضمان قراءة منفذ التشغيل الصحيح من Railway
    port = int(os.getenv("PORT", settings.PORT))

    if settings.WEBHOOK_URL and not settings.DEBUG:
        logger.info(f"🌐 Starting webhook on port {port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=f"{settings.WEBHOOK_URL}/{settings.BOT_TOKEN}"
        )
    else:
        logger.info("🔄 Starting polling mode")
        # ✅ حذف أي webhook سابق لتفادي تعارض getUpdates
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())  # ✅ تشغيل غير متزامن
