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
    """تلخيص محتوى الكتاب باستخدام الذكاء الاصطناعي"""
    query = update.callback_query
    await query.answer()

    # استخراج معرف الكتاب من بيانات الزر
    try:
        book_id = int(query.data.split("_")[2])
    except (IndexError, ValueError):
        await query.edit_message_text("⚠️ حدث خطأ في معالجة الطلب.")
        return

    db: Session = context.bot_data.get("db_session")
    if not db:
        await query.edit_message_text("❌ خطأ في الاتصال بقاعدة البيانات.")
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        await query.edit_message_text("❌ عذراً، هذا الكتاب لم يعد متاحاً.")
        return

    await query.edit_message_text("🤖 جاري استخراج المحتوى وتوليد التلخيص... يرجى الانتظار.")

    ai_service = get_ai_service()
    summary = None

    # محاولة استخراج النص من ملف PDF إذا كان متوفراً
    if book.file_id:
        try:
            # تحميل الملف من سيرفرات تليجرام
            tg_file = await context.bot.get_file(book.file_id)
            pdf_bytes = await tg_file.download_as_bytearray()

            extracted_text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                # نكتفي بأول 10 صفحات للحصول على لمحة عامة وتوفير الموارد
                for page in pdf.pages[:10]:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n" # تم إصلاح الخطأ هنا

            if extracted_text.strip():
                summary = await ai_service.summarize_text(extracted_text, max_length=500)
        except Exception as e:
            logger.error(f"Error extracting PDF text for book {book_id}: {e}")

    # إذا لم يوجد ملف أو فشل الاستخراج، نعتمد على بيانات قاعدة البيانات
    if not summary:
        context_info = f"العنوان: {book.title}. الوصف الأساسي: {book.description or 'لا يوجد وصف'}"
        summary = await ai_service.summarize_text(context_info, max_length=300)

    if summary:
        formatted_response = (
            f"📝 <b>تلخيص ذكي لكتاب: {book.title}</b>\n\n"
            f"{truncate_text(summary, 3800)}\n\n"
            f"<i>💡 تم توليد هذا الملخص آلياً وقد لا يعوض عن قراءة الكتاب كاملاً.</i>"
        )
        await query.edit_message_text(
            formatted_response,
            parse_mode="HTML",
            reply_markup=InlineKeyboards.book_details(book_id)
        )
    else:
        await query.edit_message_text(
            "❌ عذراً، واجه المساعد الذكي صعوبة في تلخيص هذا الكتاب.",
            reply_markup=InlineKeyboards.book_details(book_id)
        )


async def similar_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اقتراح كتب مشابهة من نفس القسم"""
    query = update.callback_query
    await query.answer()

    try:
        book_id = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        return

    db: Session = context.bot_data.get("db_session")
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        await query.edit_message_text("❌ الكتاب غير موجود.")
        return

    await query.edit_message_text("🔍 جاري البحث في المكتبة عن كتب مشابهة...")

    # جلب كتب من نفس التصنيف مع استبعاد الكتاب الحالي
    recommendations = db.query(Book).filter(
        Book.category_id == book.category_id,
        Book.id != book_id,
        Book.is_active == True
    ).limit(5).all()

    if recommendations:
        context.user_data["books_list"] = recommendations
        await query.edit_message_text(
            f"📚 كتب قد تعجبك في قسم <b>{book.category.name if book.category else 'القسم العام'}</b>:",
            parse_mode="HTML",
            reply_markup=InlineKeyboards.books_list(recommendations)
        )
    else:
        await query.edit_message_text(
            "😔 لم نجد كتباً مشابهة حالياً، جرب تصفح الأقسام الأخرى.",
            reply_markup=InlineKeyboards.book_details(book_id)
        )


async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تفعيل وضع المساعد الذكي للإجابة على أسئلة محددة حول الكتاب"""
    query = update.callback_query
    await query.answer()

    try:
        book_id = int(query.data.split("_")[2])
    except (IndexError, ValueError):
        return

    # حفظ معرف الكتاب في جلسة المستخدم ليعرف البوت عن أي كتاب يتم السؤال
    context.user_data["ai_assistant_book"] = book_id

    help_text = (
        f"💬 <b>المساعد الذكي نشط الآن!</b>\n\n"
        f"أنا جاهز للإجابة على أسئلتك حول محتوى هذا الكتاب.\n"
        f"<b>يمكنك سؤالي عن:</b>\n"
        f"• الدروس المستفادة من الكتاب.\n"
        f"• شرح فكرة أو فصل معين.\n"
        f"• رأي النقاد أو الجمهور.\n\n"
        f"📩 <b>أرسل سؤالك الآن مباشرة...</b>"
    )

    await query.edit_message_text(
        help_text,
        parse_mode="HTML"
    )
