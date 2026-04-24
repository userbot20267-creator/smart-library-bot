"""ملف تشغيل البوت الرئيسي"""
import logging
import os
import sys

# إضافة المسار
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

# إعداد Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

settings = get_settings()

# إنشاء قاعدة البيانات
db = Database(settings.DATABASE_URL)
db.create_tables()

# حفظ الجلسة في bot_data
async def post_init(application: Application):
    """التشغيل الأولي"""
    application.bot_data["db_session"] = db.SessionLocal()
    logger.info("✅ Bot initialized successfully")


async def post_shutdown(application: Application):
    """الإغلاق"""
    if "db_session" in application.bot_data:
        application.bot_data["db_session"].close()
    logger.info("🛑 Bot shutdown")


# Middleware wrapper
async def middleware_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تطبيق middlewares"""
    if not await rate_limit_middleware(update, context):
        return False
    return True


def main():
    """الدالة الرئيسية"""
    logger.info("🚀 Starting Smart Library Bot...")

    # إنشاء التطبيق
    application = Application.builder().token(settings.BOT_TOKEN).build()

    # إضافة post_init
    application.post_init = post_init
    application.post_shutdown = post_shutdown

    # ========== معالجات الأوامر ==========

    # أوامر المستخدم
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("me", profile_command))
    application.add_handler(CommandHandler("referral", referral_command))

    # أوامر المشرف
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("ai_search", ai_search_command))
    application.add_handler(CommandHandler("ai_insights", ai_insights_command))
    application.add_handler(CommandHandler("batch", batch_upload_start))

    # ========== معالجات المحادثة ==========

    # البحث
    search_conv = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))]
    )
    application.add_handler(search_conv)

    # إضافة كتاب
    add_book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_book_start, pattern="^admin_add_book$")],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_title)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_author)],
            3: [CallbackQueryHandler(add_book_category, pattern="^selcat_")],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_description)],
            5: [MessageHandler(filters.Document.PDF | filters.TEXT, add_book_file)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))]
    )
    application.add_handler(add_book_conv)

    # الرفع الدفعي
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
        ]
    )
    application.add_handler(batch_conv)

    # التعليقات
    comment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_comment_start, pattern="^add_comment_")],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_comment)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("تم الإلغاء"))]
    )
    application.add_handler(comment_conv)

    # ========== معالجات الأزرار ==========

    # القائمة الرئيسية
    application.add_handler(CallbackQueryHandler(browse_categories, pattern="^browse_categories$"))
    application.add_handler(CallbackQueryHandler(smart_search_callback, pattern="^smart_search$"))
    application.add_handler(CallbackQueryHandler(my_favorites, pattern="^my_favorites$"))
    application.add_handler(CallbackQueryHandler(my_downloads, pattern="^my_downloads$"))
    application.add_handler(CallbackQueryHandler(show_leaderboard, pattern="^leaderboard$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: start_command(u, c), pattern="^main_menu$"))

    # الكتب
    application.add_handler(CallbackQueryHandler(show_category_books, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(show_book_details, pattern="^book_"))
    application.add_handler(CallbackQueryHandler(download_book, pattern="^download_"))
    application.add_handler(CallbackQueryHandler(toggle_favorite, pattern="^fav_|^unfav_"))
    application.add_handler(CallbackQueryHandler(rate_book, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(share_book, pattern="^share_"))
    application.add_handler(CallbackQueryHandler(similar_books, pattern="^similar_"))
    application.add_handler(CallbackQueryHandler(ai_summary, pattern="^ai_summary_"))
    application.add_handler(CallbackQueryHandler(ai_assistant, pattern="^ai_assist_"))

    # التعليقات
    application.add_handler(CallbackQueryHandler(show_comments, pattern="^comments_"))
    application.add_handler(CallbackQueryHandler(like_comment, pattern="^like_comment_"))

    # التنقل
    application.add_handler(CallbackQueryHandler(browse_categories, pattern="^back_to_categories$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: browse_categories(u, c), pattern="^back_to_books$"))

    # الباقات
    application.add_handler(CallbackQueryHandler(browse_packs, pattern="^browse_packs$"))
    application.add_handler(CallbackQueryHandler(show_pack, pattern="^pack_"))

    # الإشعارات
    application.add_handler(CallbackQueryHandler(notification_settings, pattern="^notification_settings$"))
    application.add_handler(CallbackQueryHandler(toggle_notification, pattern="^toggle_notify_"))
    application.add_handler(CallbackQueryHandler(manage_preferred_categories, pattern="^manage_pref_cats$"))
    application.add_handler(CallbackQueryHandler(toggle_preferred_category, pattern="^prefcat_"))
    application.add_handler(CallbackQueryHandler(manage_preferred_authors, pattern="^manage_pref_authors$"))
    application.add_handler(CallbackQueryHandler(toggle_preferred_author, pattern="^prefauth_"))

    # المشرف
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

    # ========== الجدولة ==========
    scheduler = AsyncIOScheduler()

    # نسخ احتياطي يومي
    scheduler.add_job(daily_backup, "cron", hour=3, minute=0, args=[application])

    # تقرير أسبوعي (كل أحد)
    scheduler.add_job(weekly_report, "cron", day_of_week="sun", hour=9, minute=0, args=[application])

    # تذكيرات كل يوم
    scheduler.add_job(rating_reminders, "cron", hour=18, minute=0, args=[application])

    scheduler.start()

    # ========== تشغيل البوت ==========
    if settings.WEBHOOK_URL and not settings.DEBUG:
        # Webhook mode (لـ Railway)
        logger.info(f"🌐 Starting webhook on port {settings.PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=settings.PORT,
            webhook_url=f"{settings.WEBHOOK_URL}/{settings.BOT_TOKEN}"
        )
    else:
        # Polling mode (للتطوير)
        logger.info("🔄 Starting polling mode")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
