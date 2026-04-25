# الملف 49: bot/handlers/admin/ai_search.py - البحث الذكي للمالك
ai_search = """البحث الذكي وإضافة تلقائية للمالك"""
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes, ConversationTypes
from sqlalchemy.orm import Session
from bot.database.models import Book, Category, Author
from bot.services import get_ai_service
from bot.keyboards import InlineKeyboards

logger = logging.getLogger(__name__)

# حالات المحادثة
AI_SEARCH_QUERY = 1
AI_SEARCH_CONFIRM = 2


async def ai_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /ai_search للمالك"""
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
    
    # تحليل الأمر
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔍 <b>البحث الذكي</b>\n\n"
            "الاستخدام:\n"
            "<code>/ai_search اسم الكتاب --قسم اسم_القسم</code>\n\n"
            "مثال:\n"
            "<code>/ai_search الخيميائي --قسم روايات</code>\n\n"
            "أو أرسل الأمر فقط لبدء المحادثة.",
            parse_mode="HTML"
        )
        return
    
    # تحليل المعاملات
    query_text = " ".join(args)
    category_name = None
    
    if "--قسم" in query_text:
        parts = query_text.split("--قسم")
        query_text = parts[0].strip()
        category_name = parts[1].strip() if len(parts) > 1 else None
    
    await process_ai_search(update, context, query_text, category_name)


async def process_ai_search(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            query_text: str = None, category_name: str = None):
    """معالجة البحث الذكي"""
    db: Session = context.bot_data.get("db_session")
    ai_service = get_ai_service()
    
    if not db:
        return
    
    if not query_text:
        query_text = update.message.text
    
    await update.message.reply_text(f"🔍 جاري البحث عن '{query_text}'...")
    
    # البحث في المصادر الخارجية (محاكاة)
    # في الواقع يمكن الاتصال بـ OpenLibrary API أو Google Books
    search_results = await search_external_sources(query_text)
    
    if not search_results:
        await update.message.reply_text("❌ لم يتم العثور على نتائج.")
        return
    
    # عرض النتائج
    keyboard = []
    for i, result in enumerate(search_results[:5]):
        keyboard.append([InlineKeyboardButton(
            f"📖 {result['title']} - {result['author']}",
            callback_data=f"ai_add_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_ai_search")])
    
    context.user_data["ai_search_results"] = search_results
    context.user_data["ai_search_category"] = category_name
    
    await update.message.reply_text(
        "🔍 <b>نتائج البحث</b>\n\n"
        "اختر كتاباً لإضافته:\n"
        f"القسم المستهدف: {category_name or 'تلقائي'}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def search_external_sources(query: str) -> list:
    """البحث في المصادر الخارجية"""
    # محاكاة - يمكن استبدالها بـ OpenLibrary API
    # مثال: https://openlibrary.org/search.json?q=...
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openlibrary.org/search.json",
                params={"q": query, "limit": 5}
            )
            data = response.json()
            
            results = []
            for doc in data.get("docs", [])[:5]:
                results.append({
                    "title": doc.get("title", "غير معروف"),
                    "author": ", ".join(doc.get("author_name", ["غير معروف"])),
                    "year": doc.get("first_publish_year", ""),
                    "key": doc.get("key", "")
                })
            return results
    except Exception as e:
        logger.error(f"External search error: {e}")
        return []


async def confirm_ai_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد إضافة كتاب من البحث الذكي"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_ai_search":
        await query.edit_message_text("❌ تم الإلغاء.")
        return
    
    index = int(query.data.split("_")[2])
    results = context.user_data.get("ai_search_results", [])
    category_name = context.user_data.get("ai_search_category")
    
    if index >= len(results):
        await query.edit_message_text("❌ خطأ في الاختيار.")
        return
    
    result = results[index]
    db: Session = context.bot_data.get("db_session")
    
    # البحث عن المؤلف أو إنشاؤه
    author = db.query(Author).filter(Author.name == result["author"]).first()
    if not author:
        author = Author(name=result["author"])
        db.add(author)
        db.commit()
    
    # تحديد القسم
    category = None
    if category_name:
        category = db.query(Category).filter(Category.name == category_name).first()
    
    if not category:
        # اقتراح قسم تلقائي
        ai_service = get_ai_service()
        suggested = await ai_service.suggest_category(
            title=result["title"],
            author=result["author"]
        )
        if suggested:
            category = db.query(Category).filter(Category.name == suggested).first()
    
    if not category:
        category = db.query(Category).filter(Category.name == "غير مصنف").first()
        if not category:
            category = Category(name="غير مصنف")
            db.add(category)
            db.commit()
    
    # إنشاء الكتاب
    book = Book(
        title=result["title"],
        author_id=author.id,
        category_id=category.id,
        description=f"تم العثور عبر البحث الذكي. السنة: {result.get('year', 'غير معروف')}"
    )
    
    db.add(book)
    db.commit()
    
    # توليد وصف AI
    ai_service = get_ai_service()
    ai_desc = await ai_service.generate_book_description(
        title=result["title"],
        author=result["author"],
        category=category.name
    )
    
    if ai_desc:
        book.ai_description = ai_desc
        db.commit()
    
    await query.edit_message_text(
        f"✅ تم إضافة الكتاب بنجاح!\n\n"
        f"📖 {book.title}\n"
        f"✍️ {author.name}\n"
        f"📁 {category.name}\n"
        f"🆔 ID: {book.id}"
    )
    
    # تنظيف
    context.user_data.pop("ai_search_results", None)
    context.user_data.pop("ai_search_category", None)
'''

with open(f"{base_dir}/bot/handlers/admin/ai_search.py", "w", encoding="utf-8") as f:
    f.write(ai_search)

print("✅ تم إنشاء ai_search.py")
