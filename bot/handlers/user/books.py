"""معالج الكتب"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from bot.database.models import Book, Category, Author, Favorite, Download, Rating, Comment, User
from bot.keyboards import InlineKeyboards
from bot.utils import format_file_size

logger = logging.getLogger(__name__)


async def browse_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تصفح الأقسام"""
    query = update.callback_query
    await query.answer()

    db: Session = context.bot_data.get("db_session")
    if not db:
        await query.edit_message_text("❌ خطأ في الاتصال")
        return

    categories = db.query(Category).all()

    if not categories:
        await query.edit_message_text(
            "📂 لا توجد أقسام حالياً.",
            reply_markup=InlineKeyboards.main_menu()
        )
        return

    await query.edit_message_text(
        "📚 اختر القسم:",
        reply_markup=InlineKeyboards.categories_list(categories)
    )


async def show_category_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض كتب القسم"""
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    books = db.query(Book).filter(Book.category_id == category_id, Book.is_active == True).all()
    category = db.query(Category).filter(Category.id == category_id).first()

    if not books:
        await query.edit_message_text(
            f"📂 قسم '{category.name if category else 'غير معروف'}' فارغ حالياً.",
            reply_markup=InlineKeyboards.main_menu()
        )
        return

    context.user_data["current_category"] = category_id
    context.user_data["books_list"] = books

    await query.edit_message_text(
        f"📚 كتب قسم: {category.name if category else 'غير معروف'}",
        reply_markup=InlineKeyboards.books_list(books)
    )


async def show_book_details(update: Update, context: ContextTypes.DEFAULT_TYPE, book_id: int = None):
    """عرض تفاصيل الكتاب"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        book_id = int(query.data.split("_")[1])

    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        if update.callback_query:
            await query.edit_message_text("❌ الكتاب غير موجود")
        else:
            await update.message.reply_text("❌ الكتاب غير موجود")
        return

    # تحديث عدد المشاهدات
    book.view_count += 1
    db.commit()

    # التحقق من المفضلة
    is_favorite = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.book_id == book_id
    ).first() is not None

    # التحقق من المالك
    from bot.middlewares import AuthMiddleware
    is_owner = AuthMiddleware.is_owner(user.id)

    author_name = book.author.name if book.author else "غير معروف"
    category_name = book.category.name if book.category else "غير مصنف"

    book_text = f"""
📖 <b>{book.title}</b>

✍️ المؤلف: {author_name}
📁 القسم: {category_name}
⭐ التقييم: {"⭐" * int(book.average_rating)} ({book.total_ratings})
📥 التحميلات: {book.download_count}
📦 الحجم: {format_file_size(book.file_size)}

{book.description or "لا يوجد وصف"}
"""

    if update.callback_query:
        await query.edit_message_text(
            book_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboards.book_details(book_id, is_favorite, is_owner)
        )
    else:
        await update.message.reply_text(
            book_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboards.book_details(book_id, is_favorite, is_owner)
        )


async def download_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحميل الكتاب"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book or not book.file_id:
        await query.edit_message_text("❌ الكتاب غير متوفر للتحميل")
        return

    # إرسال الملف
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=book.file_id,
            caption=f"📖 {book.title}\n✍️ {book.author.name if book.author else 'غير معروف'}"
        )

        # تسجيل التحميل
        download = Download(user_id=user.id, book_id=book_id)
        db.add(download)

        book.download_count += 1

        # تحديث نقاط المستخدم
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if db_user:
            db_user.total_downloads += 1
            db_user.total_points += 5  # 5 نقاط لكل تحميل

        db.commit()

        await query.answer("✅ تم إرسال الكتاب!")

    except Exception as e:
        logger.error(f"Error sending book: {e}")
        await query.edit_message_text("❌ حدث خطأ أثناء إرسال الكتاب")


async def toggle_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة/إزالة من المفضلة"""
    query = update.callback_query
    await query.answer()

    action, book_id = query.data.split("_")[0], int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    if action == "fav":
        favorite = Favorite(user_id=user.id, book_id=book_id)
        db.add(favorite)
        db.commit()
        await query.answer("❤️ تمت الإضافة للمفضلة!")
    else:
        favorite = db.query(Favorite).filter(
            Favorite.user_id == user.id,
            Favorite.book_id == book_id
        ).first()
        if favorite:
            db.delete(favorite)
            db.commit()
        await query.answer("💔 تمت الإزالة من المفضلة!")

    # تحديث العرض
    await show_book_details(update, context, book_id)


async def rate_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تقييم الكتاب"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    book_id = int(parts[1])

    if len(parts) == 2:
        # عرض أزرار التقييم
        await query.edit_message_text(
            "⭐ اختر تقييمك:",
            reply_markup=InlineKeyboards.rating_stars(book_id)
        )
        return

    # حفظ التقييم
    rating_value = int(parts[2])
    db: Session = context.bot_data.get("db_session")
    user = update.effective_user

    if not db:
        return

    # التحقق من وجود تقييم سابق
    existing = db.query(Rating).filter(
        Rating.user_id == user.id,
        Rating.book_id == book_id
    ).first()

    if existing:
        existing.rating = rating_value
    else:
        rating = Rating(user_id=user.id, book_id=book_id, rating=rating_value)
        db.add(rating)

        # إضافة نقاط للتقييم
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if db_user:
            db_user.total_points += 3

    # تحديث متوسط التقييم
    ratings = db.query(Rating).filter(Rating.book_id == book_id).all()
    book = db.query(Book).filter(Book.id == book_id).first()
    if book and ratings:
        book.average_rating = sum(r.rating for r in ratings) / len(ratings)
        book.total_ratings = len(ratings)

    db.commit()
    await query.answer(f"⭐ تم التقييم بـ {rating_value} نجوم!")
    await show_book_details(update, context, book_id)


async def share_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مشاركة الكتاب"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split("_")[1])
    db: Session = context.bot_data.get("db_session")

    if not db:
        return

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return

    bot_info = await context.bot.get_me()
    deep_link = book.get_deep_link(bot_info.username)

    share_text = f"""
📖 شارك هذا الكتاب مع أصدقائك!

<b>{book.title}</b>
✍️ {book.author.name if book.author else 'غير معروف'}

{deep_link}
"""

    await query.edit_message_text(share_text, parse_mode="HTML")
