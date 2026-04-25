"""ميزات الذكاء الاصطناعي للمستخدم"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import Book
from bot.services import get_ai_service
from bot.keyboards import InlineKeyboards
from bot.utils import truncate_text
import pdfplumber
import io

logger = logging.getLogger(__name__)


async def ai_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تلخيص الكتاب بالذكاء الاصطناعي"""
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

    await query.edit_message_text("🤖 جاري توليد التلخيص...")

    ai_service = get_ai_service()

    # إذا كان هناك ملف PDF، استخرج النص
    if book.file_id:
        try:
            # تحميل الملف من تليجرام
            file = await context.bot.get_file(book.file_id)
            pdf_bytes = await file.download_as_bytearray()

            # استخراج النص
            text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages[:10]:  # أول 10 صفحات
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "
"

            if text:
                summary = await ai_service.summarize_text(text, max_length=400)
            else:
                # تلخيص بناءً على العنوان والوصف
                summary = await ai_service.summarize_text(
                    f"العنوان: {book.title}. الوصف: {book.description or ''}",
                    max_length=300
                )
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            summary = await ai_service.summarize_text(
                f"العنوان: {book.title}. الوصف: {book.description or ''}",
                max_length=300
            )
    else:
        summary = await ai_service.summarize_text(
            f"العنوان: {book.title}. الوصف: {book.description or ''}",
            max_length=300
        )

    if summary:
        summary_text = f"""
📝 <b>تلخيص: {book.title}</b>

{truncate_text(summary, 3900)}

<i>تم التلخيص بواسطة الذكاء الاصطناعي</i>
"""
        await query.edit_message_text(
            summary_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboards.book_details(book_id)
        )
    else:
        await query.edit_message_text(
            "❌ تعذر توليد التلخيص. حاول مرة أخرى لاحقاً.",
            reply_markup=InlineKeyboards.book_details(book_id)
        )


async def similar_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """كتب مشابهة"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        await query.edit_message_text("❌ الكتاب غير موجود")
        return

    await query.edit_message_text("🔍 جاري البحث عن كتب مشابهة...")

    # البحث عن كتب في نفس القسم
    similar = db.query(Book).filter(
        Book.category_id == book.category_id,
        Book.id != book_id,
        Book.is_active == True
    ).limit(5).all()

    if similar:
        context.user_data["books_list"] = similar
        await query.edit_message_text(
            f"📚 كتب مشابهة لـ '{book.title}':",
            reply_markup=InlineKeyboards.books_list(similar)
        )
    else:
        await query.edit_message_text(
            "❌ لا توجد كتب مشابهة حالياً.",
            reply_markup=InlineKeyboards.book_details(book_id)
        )


async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المساعد الذكي داخل الكتاب"""
    query = update.callback_query
    await query.answer()

    # تخزين حالة انتظار السؤال
    book_id = int(query.data.split("_")[2])
    context.user_data["ai_assistant_book"] = book_id

    await query.edit_message_text(
        "💬 <b>المساعد الذكي</b>

"
        "يمكنك الآن طرح أي سؤال حول محتوى هذا الكتاب.
"
        "مثال: 'ما هي الأفكار الرئيسية؟' أو 'اشرح الفصل الأول'

"
        "أرسل سؤالك الآن:",
        parse_mode="HTML"
    )
