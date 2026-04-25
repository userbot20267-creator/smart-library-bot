"""معالج البحث"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationTypes
from sqlalchemy.orm import Session
from bot.database.models import Book, Category, Author
from bot.services import get_search_engine
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)

# حالات المحادثة
SEARCH_QUERY = 1


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البحث"""
    await update.message.reply_text(
        "🔍 أرسل اسم الكتاب أو المؤلف للبحث:",
        reply_markup=InlineKeyboards.main_menu()
    )
    return SEARCH_QUERY


async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة استعلام البحث"""
    query = update.message.text
    db: Session = context.bot_data.get("db_session")

    if not db:
        await update.message.reply_text("❌ خطأ في الاتصال")
        return ConversationHandler.END

    await update.message.reply_text("🔍 جاري البحث...")

    # البحث في قاعدة البيانات المحلية
    books = db.query(Book).filter(
        Book.is_active == True,
        (Book.title.ilike(f"%{query}%")) |
        (Author.name.ilike(f"%{query}%"))
    ).join(Author).all()

    if books:
        context.user_data["books_list"] = books
        await update.message.reply_text(
            f"📚 نتائج البحث عن '{query}':",
            reply_markup=InlineKeyboards.books_list(books)
        )
    else:
        # البحث الذكي
        search_engine = get_search_engine()
        semantic_results = await search_engine.search(query, db)

        if semantic_results:
            books = [r["book"] for r in semantic_results]
            context.user_data["books_list"] = books
            await update.message.reply_text(
                f"🔍 نتائج البحث الذكي عن '{query}':",
                reply_markup=InlineKeyboards.books_list(books)
            )
        else:
            await update.message.reply_text(
                f"❌ لم يتم العثور على نتائج لـ '{query}'.",
                reply_markup=InlineKeyboards.main_menu()
            )

    return ConversationHandler.END


async def smart_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث الذكي من القائمة"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        """🔍 <b>البحث الذكي</b>

يمكنك البحث عن كتاب بالاسم، المؤلف، أو وصف عام.
مثال: 'روايات بوليسية' أو 'كتب عن التطوير الذاتي'

أرسل استعلامك الآن:""",
        parse_mode="HTML"
    )
    context.user_data["awaiting_smart_search"] = True
    
