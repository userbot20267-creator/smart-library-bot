"""لوحة تحكم المالك والمشرفين"""
import logging
import csv
import io
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from bot.database.models import User, Category, Author, Book, RequiredChannel
from bot.middlewares import AuthMiddleware
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)

# حالات المحادثة
ADMIN_ACTION = 1
BROADCAST_MESSAGE = 2
ADD_CATEGORY = 3
ADD_BOOK_TITLE = 4
ADD_BOOK_AUTHOR = 5
ADD_BOOK_FILE = 6


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المشرف"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")

    if not db:
        await update.message.reply_text("❌ خطأ في الاتصال")
        return

    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    if not db_user or not AuthMiddleware.is_admin(db_user):
        await update.message.reply_text("🚷 ليس لديك صلاحية الوصول.")
        return

    # الإصلاح هنا: استخدام علامات التنصيص الثلاثية للنصوص متعددة الأسطر
    await update.message.reply_text(
        """👑 <b>لوحة التحكم</b>

اختر القسم:""",
        parse_mode="HTML",
        reply_markup=InlineKeyboards.admin_menu()
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات المكتبة"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    total_users = db.query(User).count()
    total_books = db.query(Book).count()
    total_categories = db.query(Category).count()
    total_authors = db.query(Author).count()
    total_downloads = db.query(Book).with_entities(Book.download_count).all()
    total_downloads_sum = sum(d[0] for d in total_downloads if d[0])

    # أكثر الكتب تحميلاً
    top_books = db.query(Book).order_by(Book.download_count.desc()).limit(5).all()

    stats_text = f"""
📊 <b>إحصائيات المكتبة</b>

👥 المستخدمين: {total_users}
📚 الكتب: {total_books}
📁 الأقسام: {total_categories}
✍️ المؤلفين: {total_authors}
📥 إجمالي التحميلات: {total_downloads_sum}

🏆 <b>أكثر الكتب تحميلاً:</b>
"""
    for i, book in enumerate(top_books, 1):
        stats_text += f"{i}. {book.title} ({book.download_count} تحميل)\n"

    await query.edit_message_text(stats_text, parse_mode="HTML", reply_markup=InlineKeyboards.admin_menu())


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة المستخدمين"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    users = db.query(User).limit(20).all()

    text = "👥 <b>المستخدمين</b>\n\n"
    for user in users:
        status = "🚷" if user.is_banned else "✅"
        text += f"{status} {user.first_name or 'مستخدم'} - ID: {user.telegram_id} - نقاط: {user.total_points}\n"

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboards.admin_menu())


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء الإذاعة"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📢 أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:\n\n"
        "أو اضغط /cancel للإلغاء."
    )
    return BROADCAST_MESSAGE


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال الإذاعة"""
    message = update.message.text
    db: Session = context.bot_data.get("db_session")

    if not db:
        await update.message.reply_text("❌ خطأ")
        return ConversationHandler.END

    users = db.query(User).filter(User.is_banned == False).all()
    sent = 0
    failed = 0

    await update.message.reply_text(f"⏳ جاري الإرسال لـ {len(users)} مستخدم...")

    for user in users:
        try:
            await context.bot.send_message(user.telegram_id, message)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ تم الإرسال!\n"
        f"📤 نجح: {sent}\n"
        f"❌ فشل: {failed}"
    )

    return ConversationHandler.END


async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تصدير بيانات المستخدمين"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    users = db.query(User).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Username", "First Name", "Last Name", "Points", "Downloads", "Joined"])

    for user in users:
        writer.writerow([
            user.telegram_id,
            user.username,
            user.first_name,
            user.last_name,
            user.total_points,
            user.total_downloads,
            user.created_at
        ])

    output.seek(0)

    await context.bot.send_document(
        chat_id=update.effective_user.id,
        document=output.getvalue().encode(),
        filename="users_export.csv",
        caption="📊 تصدير بيانات المستخدمين"
    )
    
