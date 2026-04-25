"""إدارة الكتب المتقدمة للمالك"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationTypes
from sqlalchemy.orm import Session
from bot.database.models import Book, Category, Author
from bot.services import get_ai_service
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)

# حالات المحادثة
BOOK_TITLE = 1
BOOK_AUTHOR = 2
BOOK_CATEGORY = 3
BOOK_DESCRIPTION = 4
BOOK_FILE = 5
EDIT_BOOK_SELECT = 6
EDIT_BOOK_FIELD = 7


async def admin_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة إدارة الكتب"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة كتاب يدوي", callback_data="admin_add_book")],
        [InlineKeyboardButton("🔍 بحث وإضافة كتاب", callback_data="admin_search_add")],
        [InlineKeyboardButton("📋 عرض جميع الكتب", callback_data="admin_list_books")],
        [InlineKeyboardButton("🤖 توليد وصف AI", callback_data="admin_ai_desc")],
        [InlineKeyboardButton("🔄 إعادة تصنيف AI", callback_data="admin_ai_recategorize")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]

    await query.edit_message_text(
        """📚 <b>إدارة الكتب</b>

اختر الإجراء:""",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة كتاب"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        """📖 <b>إضافة كتاب جديد</b>

أرسل عنوان الكتاب:
أو اضغط /cancel للإلغاء."""
    )
    return BOOK_TITLE


async def add_book_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام عنوان الكتاب"""
    context.user_data["new_book_title"] = update.message.text

    await update.message.reply_text(
        """✍️ أرسل اسم المؤلف:
أو اضغط /skip لتخطي."""
    )
    return BOOK_AUTHOR


async def add_book_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام اسم المؤلف"""
    db: Session = context.bot_data.get("db_session")
    author_name = update.message.text

    if author_name != "/skip":
        # البحث عن المؤلف أو إنشاؤه
        author = db.query(Author).filter(Author.name == author_name).first()
        if not author:
            author = Author(name=author_name)
            db.add(author)
            db.commit()
        context.user_data["new_book_author_id"] = author.id

    # عرض الأقسام
    categories = db.query(Category).all()
    keyboard = [[InlineKeyboardButton(cat.name, callback_data=f"selcat_{cat.id}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("🆕 قسم جديد", callback_data="new_category")])

    await update.message.reply_text(
        "📁 اختر القسم:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOOK_CATEGORY


async def add_book_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار القسم"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("selcat_"):
        category_id = int(query.data.split("_")[1])
        context.user_data["new_book_category_id"] = category_id

    await query.edit_message_text(
        """📝 أرسل وصف الكتاب (اختياري):
أو اضغط /skip."""
    )
    return BOOK_DESCRIPTION


async def add_book_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام الوصف"""
    description = update.message.text if update.message.text != "/skip" else ""
    context.user_data["new_book_description"] = description

    # توليد وصف AI
    ai_service = get_ai_service()
    title = context.user_data.get("new_book_title", "")

    await update.message.reply_text(
        "🤖 جاري توليد وصف ذكي..."
    )

    ai_desc = await ai_service.generate_book_description(
        title=title,
        author="",
        category=""
    )

    if ai_desc:
        context.user_data["new_book_ai_description"] = ai_desc
        await update.message.reply_text(
            f"""🤖 <b>وصف مقترح:</b>
{ai_desc}

هل تريد استخدامه؟ (نعم/لا)""",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            """📎 أرسل ملف PDF أو رابط الكتاب:
أو اضغط /skip."""
        )

    return BOOK_FILE


async def add_book_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام ملف الكتاب"""
    db: Session = context.bot_data.get("db_session")

    title = context.user_data.get("new_book_title")
    author_id = context.user_data.get("new_book_author_id")
    category_id = context.user_data.get("new_book_category_id")
    description = context.user_data.get("new_book_description", "")
    ai_description = context.user_data.get("new_book_ai_description", "")

    file_id = None
    file_size = 0

    if update.message.document:
        file_id = update.message.document.file_id
        file_size = update.message.document.file_size or 0
    elif update.message.text and update.message.text != "/skip":
        file_url = update.message.text

    # إنشاء الكتاب
    book = Book(
        title=title,
        description=description or ai_description,
        ai_description=ai_description,
        author_id=author_id,
        category_id=category_id,
        file_id=file_id,
        file_size=file_size
    )

    db.add(book)
    db.commit()

    await update.message.reply_text(
        f"""✅ تم إضافة الكتاب '{title}' بنجاح!
🆔 ID: {book.id}"""
    )

    # تنظيف
    for key in ["new_book_title", "new_book_author_id", "new_book_category_id", 
                "new_book_description", "new_book_ai_description"]:
        context.user_data.pop(key, None)

    return ConversationHandler.END


async def list_all_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع الكتب للمالك"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    books = db.query(Book).order_by(Book.created_at.desc()).limit(20).all()

    if not books:
        await query.edit_message_text("📚 لا توجد كتب.")
        return

    text = "📚 <b>جميع الكتب</b>\n\n"
    for book in books:
        author = book.author.name if book.author else "غير معروف"
        category = book.category.name if book.category else "غير مصنف"
        status = "✅" if book.is_active else "❌"
        text += f"{status} 🆔{book.id} | {book.title}\n"
        text += f"   ✍️ {author} | 📁 {category} | 📥 {book.download_count}\n\n"

    keyboard = [
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="admin_advanced_search")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_books")]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def advanced_search_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بحث متقدم في الكتب"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📁 حسب القسم", callback_data="search_filter_category")],
        [InlineKeyboardButton("✍️ حسب المؤلف", callback_data="search_filter_author")],
        [InlineKeyboardButton("📅 حسب التاريخ", callback_data="search_filter_date")],
        [InlineKeyboardButton("📄 حسب النوع", callback_data="search_filter_type")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_list_books")]
    ]

    await query.edit_message_text(
        """🔍 <b>البحث المتقدم</b>

اختر الفلتر:""",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def ai_recategorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تصنيف ذكية للكتب"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        return

    # البحث عن كتب غير مصنفة أو في قسم "غير مصنف"
    uncategorized = db.query(Book).filter(
        (Book.category_id == None) | 
        (Category.name == "غير مصنف")
    ).join(Category, isouter=True).limit(10).all()

    if not uncategorized:
        await query.edit_message_text("✅ لا توجد كتب غير مصنفة!")
        return

    ai_service = get_ai_service()

    await query.edit_message_text("🤖 جاري تحليل الكتب واقتراح الأقسام...")

    results = []
    for book in uncategorized:
        suggested = await ai_service.suggest_category(
            title=book.title,
            author=book.author.name if book.author else "",
            description=book.description or ""
        )

        if suggested:
            # البحث عن القسم المقترح
            category = db.query(Category).filter(Category.name == suggested).first()
            if category:
                book.category_id = category.id
                results.append(f"✅ '{book.title}' → {category.name}")
            else:
                results.append(f"⚠️ '{book.title}' → قسم '{suggested}' غير موجود")

    db.commit()

    text = "🤖 <b>نتائج إعادة التصنيف</b>\n\n"
    text += "\n".join(results[:20])

    await context.bot.send_message(
        update.effective_user.id,
        text,
        parse_mode="HTML"
    )
