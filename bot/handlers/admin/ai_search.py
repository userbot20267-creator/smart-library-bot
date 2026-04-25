import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from bot.database.models import Book, Category, Author, User  # أضفنا User هنا
from bot.services import get_ai_service

logger = logging.getLogger(__name__)

# حالات المحادثة (Conversation States)
AI_SEARCH_QUERY = 1

async def ai_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /ai_search للمالك للبحث الذكي عن الكتب"""
    user = update.effective_user
    db: Session = context.bot_data.get("db_session")
    
    if not db:
        await update.message.reply_text("❌ خطأ: لا يوجد اتصال بقاعدة البيانات.")
        return ConversationHandler.END
    
    # التحقق من الصلاحيات (Admin)
    from bot.middlewares import AuthMiddleware
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not db_user or not AuthMiddleware.is_admin(db_user):
        await update.message.reply_text("🚷 هذا الأمر مخصص للإدارة فقط.")
        return ConversationHandler.END
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔍 <b>البحث الذكي</b>\n\n"
            "الاستخدام:\n"
            "<code>/ai_search اسم الكتاب --قسم اسم_القسم</code>\n\n"
            "أو أرسل اسم الكتاب الآن للبحث عنه:",
            parse_mode="HTML"
        )
        return AI_SEARCH_QUERY
    
    # تحليل المعاملات من نص الأمر
    query_text = " ".join(args)
    category_name = None
    
    if "--قسم" in query_text:
        parts = query_text.split("--قسم")
        query_text = parts[0].strip()
        category_name = parts[1].strip() if len(parts) > 1 else None
    
    return await process_ai_search(update, context, query_text, category_name)


async def process_ai_search(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            query_text: str = None, category_name: str = None):
    """جلب النتائج من OpenLibrary وعرضها"""
    if not query_text:
        query_text = update.message.text

    msg = await update.message.reply_text(f"🔍 جاري البحث عن '{query_text}' في المصادر العالمية...")
    
    # البحث في OpenLibrary API
    search_results = await _search_external_sources(query_text)
    
    if not search_results:
        await msg.edit_text("❌ لم يتم العثور على نتائج تطابق هذا العنوان.")
        return ConversationHandler.END
    
    # بناء لوحة الأزرار بالنتائج
    keyboard = []
    for i, result in enumerate(search_results[:5]):
        keyboard.append([InlineKeyboardButton(
            f"📖 {result['title']} ({result['year']})",
            callback_data=f"ai_add_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_ai_search")])
    
    # تخزين النتائج مؤقتاً في سياق المستخدم
    context.user_data["ai_search_results"] = search_results
    context.user_data["ai_search_category"] = category_name
    
    await msg.edit_text(
        "🔍 <b>نتائج البحث الذكي</b>\n\n"
        "اختر الكتاب الذي تود إضافته آلياً:\n"
        f"القسم المستهدف: {category_name or 'تلقائي (AI)'}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END # ننهي الحالة لأن المعالجة التالية ستكون عبر CallbackQuery


async def _search_external_sources(query: str) -> list:
    """دالة مساعدة للبحث في OpenLibrary API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openlibrary.org/search.json",
                params={"q": query, "limit": 5},
                timeout=10.0
            )
            data = response.json()
            
            results = []
            for doc in data.get("docs", []):
                results.append({
                    "title": doc.get("title", "غير معروف"),
                    "author": ", ".join(doc.get("author_name", ["مؤلف مجهول"])),
                    "year": doc.get("first_publish_year", "N/A"),
                    "key": doc.get("key", "")
                })
            return results
    except Exception as e:
        logger.error(f"External search error: {e}")
        return []


async def confirm_ai_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على زر الإضافة"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_ai_search":
        await query.edit_message_text("❌ تم إلغاء عملية البحث.")
        return
    
    # استخراج البيانات المخزنة
    index = int(query.data.split("_")[2])
    results = context.user_data.get("ai_search_results", [])
    category_name = context.user_data.get("ai_search_category")
    
    if not results or index >= len(results):
        await query.edit_message_text("❌ انتهت صلاحية هذه النتائج، حاول البحث مجدداً.")
        return

    result = results[index]
    db: Session = context.bot_data.get("db_session")
    
    # 1. إدارة المؤلف
    author = db.query(Author).filter(Author.name == result["author"]).first()
    if not author:
        author = Author(name=result["author"])
        db.add(author)
        db.flush() # للحصول على ID قبل الـ commit
    
    # 2. إدارة القسم
    category = None
    if category_name:
        category = db.query(Category).filter(Category.name == category_name).first()
    
    if not category:
        ai_service = get_ai_service()
        suggested = await ai_service.suggest_category(result["title"], result["author"])
        category = db.query(Category).filter(Category.name == suggested).first() if suggested else None
    
    if not category:
        category = db.query(Category).filter(Category.name == "غير مصنف").first()
        if not category:
            category = Category(name="غير مصنف")
            db.add(category)
            db.flush()

    # 3. إنشاء الكتاب
    new_book = Book(
        title=result["title"],
        author_id=author.id,
        category_id=category.id,
        description=f"كتاب مضاف آلياً. سنة النشر: {result['year']}"
    )
    db.add(new_book)
    db.commit()
    
    # 4. توليد وصف ذكي (اختياري خلف الكواليس)
    ai_service = get_ai_service()
    ai_desc = await ai_service.generate_book_description(result["title"], result["author"], category.name)
    if ai_desc:
        new_book.ai_description = ai_desc
        db.commit()
    
    await query.edit_message_text(
        f"✅ <b>تمت الإضافة بنجاح!</b>\n\n"
        f"📖 الكتاب: {new_book.title}\n"
        f"✍️ المؤلف: {author.name}\n"
        f"📁 القسم: {category.name}\n"
        f"🆔 المعرف: {new_book.id}",
        parse_mode="HTML"
    )
    
    # تنظيف البيانات المؤقتة
    context.user_data.pop("ai_search_results", None)
    context.user_data.pop("ai_search_category", None)
    
