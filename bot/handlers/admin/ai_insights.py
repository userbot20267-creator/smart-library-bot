"""تحليل المكتبة بالذكاء الاصطناعي"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from sqlalchemy import func
from bot.database.models import Book, Category, User, Download
from bot.services import get_ai_service
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)


async def ai_insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /ai_insights للمالك"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")

    if not db:
        await update.message.reply_text("❌ خطأ")
        return

    from bot.middlewares import AuthMiddleware
    db_user = db.query(User).filter(User.telegram_id == user.id).first()

    if not db_user or not AuthMiddleware.is_admin(db_user):
        await update.message.reply_text("🚷 ليس لديك صلاحية.")
        return

    await update.message.reply_text("🤖 جاري تحليل المكتبة... قد يستغرق هذا بضع دقائق.")

    # جمع البيانات بكفاءة أعلى
    total_books = db.query(Book).count()
    total_categories = db.query(Category).count()
    total_users = db.query(User).count()
    total_downloads = db.query(Download).count()

    # أكثر الكتب تحميلاً
    top_books = db.query(Book).order_by(Book.download_count.desc()).limit(10).all()

    # إحصائيات الأقسام (تم تحسينها لتتم داخل قاعدة البيانات)
    cat_results = db.query(Category.name, func.sum(Book.download_count)).join(Book).group_by(Category.name).all()
    category_stats = {name: int(count) for name, count in cat_results}

    # كتب بدون وصف
    books_no_desc = db.query(Book).filter(
        (Book.description == None) | (Book.description == "")
    ).count()

    # كتب غير مصنفة
    uncategorized = db.query(Book).filter(Book.category_id == None).count()

    # إعداد البيانات للـ AI
    books_data = {
        "total_books": total_books,
        "total_categories": total_categories,
        "total_users": total_users,
        "total_downloads": total_downloads,
        "top_books": [{"title": b.title, "downloads": b.download_count} for b in top_books],
        "category_stats": category_stats,
        "books_no_description": books_no_desc,
        "uncategorized_books": uncategorized
    }

    ai_service = get_ai_service()
    analysis = await ai_service.analyze_library([books_data])

    if analysis:
        # تصحيح علامات التنصيص هنا باستخدام الثلاثية
        text = f"""
🤖 <b>تحليل المكتبة بالذكاء الاصطناعي</b>

📊 <b>الإحصائيات الأساسية:</b>
• 📚 الكتب: {total_books}
• 📁 الأقسام: {total_categories}
• 👥 المستخدمين: {total_users}
• 📥 التحميلات: {total_downloads}
• ⚠️ كتب بدون وصف: {books_no_desc}
• 📂 كتب غير مصنفة: {uncategorized}

📝 <b>التحليل الذكي:</b>
{analysis}
"""
    else:
        text = "❌ تعذر إنشاء التحليل. حاول مرة أخرى."

    await update.message.reply_text(text, parse_mode="HTML")


async def generate_description_for_existing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توليد وصف لكتاب موجود"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[2])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        await query.edit_message_text("❌ الكتاب غير موجود")
        return

    await query.edit_message_text("🤖 جاري توليد وصف...")

    ai_service = get_ai_service()
    description = await ai_service.generate_book_description(
        title=book.title,
        author=book.author.name if book.author else "",
        category=book.category.name if book.category else ""
    )

    if description:
        book.ai_description = description
        db.commit()

        # تصحيح علامات التنصيص هنا
        await query.edit_message_text(
            f"""🤖 <b>وصف مقترح لـ '{book.title}':</b>

{description}

هل تريد حفظه؟""",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ حفظ", callback_data=f"save_desc_{book_id}")],
                [InlineKeyboardButton("❌ تجاهل", callback_data=f"book_{book_id}")]
            ])
        )
    else:
        await query.edit_message_text("❌ تعذر توليد الوصف.")


async def save_ai_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ الوصف المولد"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[2])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if book and book.ai_description:
        book.description = book.ai_description
        db.commit()
        await query.edit_message_text("✅ تم حفظ الوصف!")
    else:
        await query.edit_message_text("❌ خطأ.")
